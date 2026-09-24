# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import smtplib
import socket
import threading
import time

from garlicsmtp.application import ApplicationBuilder
from garlicsmtp.configuration import (
    ApplicationPaths,
    ApplicationSettings,
)
from garlicsmtp.security.auth import MemoryAuthenticator
from garlicsmtp.core.pipeline import Pipeline, PipelineContext, LoggerStage
from garlicsmtp.queue.manager import QueueManager
from garlicsmtp.queue.serializer import QueueSerializer
from garlicsmtp.queue.stage import QueueStage
from garlicsmtp.queue.worker import QueueWorker
from garlicsmtp.transport.local.transport import LocalTransport
from garlicsmtp.transport.manager import TransportManager


def test_end_to_end(tmp_path, message):

    queue = QueueManager()

    pipeline = Pipeline()
    pipeline.add(LoggerStage())
    pipeline.add(QueueStage(queue))

    context = PipelineContext(message)

    pipeline.execute(context)

    assert queue.size() == 1

    transport = LocalTransport(tmp_path)
    manager = TransportManager(transport)

    worker = QueueWorker(
        queue,
        manager,
    )

    assert worker.process() is True

    assert queue.size() == 0

    files = list(tmp_path.glob("*.json"))

    assert len(files) == 1

    loaded = QueueSerializer.from_json(
        files[0].read_text(encoding="utf-8")
    )

    assert loaded.id

    assert loaded.message.envelope.sender == (
        message.envelope.sender
    )

    assert loaded.message.envelope.recipients == (
        message.envelope.recipients
    )

    assert loaded.message.headers.fields == (
        message.headers.fields
    )

    assert loaded.message.body == (
        message.body
    )


def receive_line(client):
    data = bytearray()

    while not data.endswith(b"\r\n"):
        chunk = client.recv(1)

        if not chunk:
            break

        data.extend(chunk)

    return data.decode("utf-8")


def test_smtp_delivery_is_visible_through_imap(
    tmp_path,
):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )

    settings = ApplicationSettings()
    settings.tor.enabled = False
    settings.smtp.port = 0
    settings.imap.port = 0

    context = ApplicationBuilder(
        paths=paths,
        settings=settings,
        imap_authenticator=MemoryAuthenticator(
            {
                "alice": "secret",
            }
        ),
    ).build()

    context.smtp_server.start()
    context.imap_server.start()

    smtp_port = (
        context.smtp_server.server.socket
        .getsockname()[1]
    )
    imap_port = (
        context.imap_server.server.socket
        .getsockname()[1]
    )

    stop_event = threading.Event()

    def run_servers():
        while not stop_event.is_set():
            context.smtp_server.tick()
            context.imap_server.tick()
            time.sleep(0.01)

    thread = threading.Thread(
        target=run_servers,
        daemon=True,
    )
    thread.start()

    try:
        with smtplib.SMTP(
            "127.0.0.1",
            smtp_port,
            timeout=5,
        ) as client:
            client.ehlo("client.local")
            client.mail("alice@test.onion")
            client.rcpt("bob@test.onion")
            client.data(
                "Subject: SMTP to IMAP\r\n"
                "\r\n"
                "Visible through IMAP"
            )

        with socket.create_connection(
            ("127.0.0.1", imap_port),
            timeout=5,
        ) as client:
            assert receive_line(client) == (
                "* OK IMAP ready\r\n"
            )

            client.sendall(
                b"A001 LOGIN alice secret\r\n"
            )

            assert receive_line(client) == (
                "A001 OK LOGIN completed\r\n"
            )

            client.sendall(
                b'A002 SELECT "bob@test.onion"\r\n'
            )

            select_lines = []

            while True:
                line = receive_line(client)
                select_lines.append(line)

                if line.startswith("A002 "):
                    break

            assert "* 1 EXISTS\r\n" in select_lines
            assert select_lines[-1] == (
                "A002 OK [READ-WRITE] "
                "SELECT completed\r\n"
            )

            client.sendall(
                b"A003 UID FETCH 1 BODY[]\r\n"
            )

            fetch_line = receive_line(client)

            assert fetch_line.startswith(
                "* 1 FETCH "
            )
            assert "BODY[]" in fetch_line

            literal_start = fetch_line.rfind("{")
            literal_end = fetch_line.rfind("}")

            assert literal_start != -1
            assert literal_end != -1

            literal_size = int(
                fetch_line[
                    literal_start + 1:
                    literal_end
                ]
            )

            content = bytearray()

            while len(content) < literal_size:
                chunk = client.recv(
                    literal_size - len(content)
                )

                if not chunk:
                    break

                content.extend(chunk)

            message = content.decode("utf-8")

            assert (
                "Subject: SMTP to IMAP"
                in message
            )
            assert (
                "Visible through IMAP"
                in message
            )
            assert receive_line(client) == "\r\n"
            assert receive_line(client) == ")\r\n"

            assert receive_line(client) == (
                "A003 OK UID FETCH completed\r\n"
            )

            client.sendall(
                b"A004 LOGOUT\r\n"
            )

            assert receive_line(client) == (
                "* BYE Logging out\r\n"
            )

            assert receive_line(client) == (
                "A004 OK LOGOUT completed\r\n"
            )

    finally:
        stop_event.set()

        context.smtp_server.stop()
        context.imap_server.stop()

        thread.join(timeout=2)

        context.queue.backend.close()
        context.store.backend.close()