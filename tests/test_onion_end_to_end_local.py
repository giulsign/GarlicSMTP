# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import socket
import threading
import time

from garlicsmtp.core.pipeline import (
    LoggerStage,
    Pipeline,
)
from garlicsmtp.models import (
    Envelope,
    MailHeaders,
    MailMessage,
)
from garlicsmtp.queue.factory import QueueFactory
from garlicsmtp.queue.manager import QueueManager
from garlicsmtp.queue.sqlite import SQLiteQueueBackend
from garlicsmtp.queue.stage import QueueStage
from garlicsmtp.smtp.server import SMTPServer
from garlicsmtp.transport.onion.transport import OnionTransport


class LocalSocksConnection:

    def __init__(
        self,
        host: str,
        port: int,
    ):
        self.socket = socket.create_connection(
            (host, port),
            timeout=5,
        )

    def close(self):
        self.socket.close()


class LocalSocksClient:

    def __init__(
        self,
        host: str,
        port: int,
    ):
        self.host = host
        self.port = port
        self.calls = []

    def connect(
        self,
        onion_host: str,
        onion_port: int,
    ):
        self.calls.append(
            (onion_host, onion_port)
        )

        return LocalSocksConnection(
            self.host,
            self.port,
        )


def test_onion_transport_delivers_to_real_smtp_server(
    tmp_path,
):

    host = "a" * 56 + ".onion"
    port = 2532

    backend = SQLiteQueueBackend(
        tmp_path / "receiver.db"
    )

    queue = QueueManager(
        backend=backend,
    )

    pipeline = Pipeline()
    pipeline.add(LoggerStage())
    pipeline.add(QueueStage(queue))

    server = SMTPServer(
        host="127.0.0.1",
        port=port,
        hostname=host,
        pipeline=pipeline,
    )

    server.start()

    stop_event = threading.Event()

    def run_server():
        while not stop_event.is_set():
            server.tick()
            time.sleep(0.01)

    server_thread = threading.Thread(
        target=run_server,
        daemon=True,
    )

    server_thread.start()

    try:
        socks = LocalSocksClient(
            "127.0.0.1",
            port,
        )

        transport = OnionTransport(
            socks_client=socks,
        )

        message = MailMessage(
            envelope=Envelope(
                sender="alice@sender.onion",
                recipients=[
                    f"bob@{host}"
                ],
            ),
            headers=MailHeaders(
                fields={
                    "Subject": "Local E2E",
                }
            ),
            body="Hello local onion flow",
        )

        item = QueueFactory.create(
            message
        )

        assert transport.deliver(item) is True

        deadline = time.monotonic() + 2.0

        while (
            queue.size() == 0
            and time.monotonic() < deadline
        ):
            time.sleep(0.01)

        assert queue.size() == 1

        received = queue.peek()

        assert received is not None
        assert received.message is not None

        assert (
            received.message.envelope.sender
            == "alice@sender.onion"
        )

        assert (
            received.message.envelope.recipients
            == [f"bob@{host}"]
        )

        assert (
            received.message.headers.fields.get(
                "Subject"
            )
            == "Local E2E"
        )

        assert (
            received.message.body
            == "Hello local onion flow"
        )

        assert socks.calls == [
            (host, 25)
        ]

    finally:
        stop_event.set()
        server.stop()
        server_thread.join(timeout=2)
        backend.close()