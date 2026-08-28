# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.core.pipeline import Pipeline
from garlicsmtp.queue.manager import QueueManager
from garlicsmtp.queue.stage import QueueStage
from garlicsmtp.smtp.connection import SMTPConnection
from garlicsmtp.smtp.protocol import SMTPProtocol


class FakeSocket:

    def __init__(self):
        self.sent = b""
        self.buffer = []

    def sendall(self, data):
        self.sent += data

    def recv(self, size):
        if self.buffer:
            return self.buffer.pop(0)

        return b""

    def close(self):
        pass


def build_empty_pipeline() -> Pipeline:
    return Pipeline()


def build_queue_pipeline() -> tuple[
    Pipeline,
    QueueManager,
]:
    queue = QueueManager()

    pipeline = Pipeline()
    pipeline.add(
        QueueStage(queue)
    )

    return pipeline, queue


def create_protocol(
    connection: SMTPConnection,
    hostname: str = "localhost",
) -> SMTPProtocol:
    return SMTPProtocol(
        connection,
        hostname=hostname,
        pipeline=build_empty_pipeline(),
    )


def test_protocol_greeting():
    connection = SMTPConnection(
        FakeSocket(),
        ("127.0.0.1", 2525),
    )

    protocol = create_protocol(
        connection,
        hostname="garlicsmtp.onion",
    )

    protocol.send_greeting()

    assert connection.client.sent == (
        b"220 garlicsmtp.onion "
        b"GarlicSMTP ready\r\n"
    )


def test_protocol_receive_command():
    sock = FakeSocket()

    sock.buffer = [
        b"EHLO test.onion\r\n",
    ]

    connection = SMTPConnection(
        sock,
        ("127.0.0.1", 2525),
    )

    protocol = create_protocol(
        connection
    )

    assert (
        protocol.receive_command()
        == "EHLO test.onion"
    )


def test_protocol_process_one_command_ok():
    sock = FakeSocket()

    sock.buffer = [
        b"EHLO test.onion\r\n",
    ]

    connection = SMTPConnection(
        sock,
        ("127.0.0.1", 2525),
    )

    protocol = create_protocol(
        connection
    )

    assert protocol.process_one_command() is True

    assert sock.sent == (
        b"250 Hello test.onion\r\n"
    )


def test_protocol_process_one_command_quit():
    sock = FakeSocket()

    sock.buffer = [
        b"QUIT\r\n",
    ]

    connection = SMTPConnection(
        sock,
        ("127.0.0.1", 2525),
    )

    protocol = create_protocol(
        connection
    )

    assert protocol.process_one_command() is False
    assert sock.sent == b"221 Bye\r\n"


def test_protocol_serve_ehlo_quit():
    sock = FakeSocket()

    sock.buffer = [
        b"EHLO test.onion\r\n",
        b"QUIT\r\n",
    ]

    connection = SMTPConnection(
        sock,
        ("127.0.0.1", 2525),
    )

    protocol = create_protocol(
        connection,
        hostname="garlicsmtp.onion",
    )

    protocol.serve()

    assert sock.sent == (
        b"220 garlicsmtp.onion "
        b"GarlicSMTP ready\r\n"
        b"250 Hello test.onion\r\n"
        b"221 Bye\r\n"
    )


def test_protocol_ehlo_mail_quit():
    sock = FakeSocket()

    sock.buffer = [
        b"EHLO client.onion\r\n",
        b"MAIL FROM:<alice@test.onion>\r\n",
        b"QUIT\r\n",
    ]

    connection = SMTPConnection(
        sock,
        ("127.0.0.1", 2525),
    )

    protocol = create_protocol(
        connection,
        hostname="garlicsmtp.onion",
    )

    protocol.serve()

    assert (
        protocol.session.message.envelope.sender
        == "alice@test.onion"
    )

    assert sock.sent == (
        b"220 garlicsmtp.onion "
        b"GarlicSMTP ready\r\n"
        b"250 Hello client.onion\r\n"
        b"250 Sender OK\r\n"
        b"221 Bye\r\n"
    )


def test_protocol_ehlo_mail_rcpt_quit():
    sock = FakeSocket()

    sock.buffer = [
        b"EHLO client.onion\r\n",
        b"MAIL FROM:<alice@test.onion>\r\n",
        b"RCPT TO:<bob@test.onion>\r\n",
        b"QUIT\r\n",
    ]

    connection = SMTPConnection(
        sock,
        ("127.0.0.1", 2525),
    )

    protocol = create_protocol(
        connection,
        hostname="garlicsmtp.onion",
    )

    protocol.serve()

    assert (
        protocol.session.message.envelope.sender
        == "alice@test.onion"
    )

    assert (
        protocol.session.message.envelope.recipients
        == [
            "bob@test.onion",
        ]
    )

    assert sock.sent == (
        b"220 garlicsmtp.onion "
        b"GarlicSMTP ready\r\n"
        b"250 Hello client.onion\r\n"
        b"250 Sender OK\r\n"
        b"250 Recipient OK\r\n"
        b"221 Bye\r\n"
    )


def test_protocol_data_body_quit():
    sock = FakeSocket()

    sock.buffer = [
        b"EHLO client.onion\r\n",
        b"MAIL FROM:<alice@test.onion>\r\n",
        b"RCPT TO:<bob@test.onion>\r\n",
        b"DATA\r\n",
        b"Subject: Test\r\n",
        b"\r\n",
        b"Hello Bob\r\n",
        b".\r\n",
        b"QUIT\r\n",
    ]

    connection = SMTPConnection(
        sock,
        ("127.0.0.1", 2525),
    )

    protocol = create_protocol(
        connection,
        hostname="garlicsmtp.onion",
    )

    protocol.serve()

    assert (
        protocol.session.message.headers.get(
            "Subject"
        )
        == "Test"
    )

    assert (
        protocol.session.message.body
        == "Hello Bob"
    )

    assert sock.sent == (
        b"220 garlicsmtp.onion "
        b"GarlicSMTP ready\r\n"
        b"250 Hello client.onion\r\n"
        b"250 Sender OK\r\n"
        b"250 Recipient OK\r\n"
        b"354 End data with "
        b"<CR><LF>.<CR><LF>\r\n"
        b"250 Message accepted\r\n"
        b"221 Bye\r\n"
    )


def test_protocol_data_queues_message():
    sock = FakeSocket()

    sock.buffer = [
        b"EHLO client.onion\r\n",
        b"MAIL FROM:<alice@test.onion>\r\n",
        b"RCPT TO:<bob@test.onion>\r\n",
        b"DATA\r\n",
        b"Subject: Queue Test\r\n",
        b"\r\n",
        b"Hello Queue\r\n",
        b".\r\n",
        b"QUIT\r\n",
    ]

    connection = SMTPConnection(
        sock,
        ("127.0.0.1", 2525),
    )

    pipeline, queue = (
        build_queue_pipeline()
    )

    protocol = SMTPProtocol(
        connection,
        hostname="garlicsmtp.onion",
        pipeline=pipeline,
    )

    protocol.serve()

    assert queue.size() == 1

    item = queue.dequeue()

    assert (
        item.message.envelope.sender
        == "alice@test.onion"
    )

    assert (
        item.message.envelope.recipients
        == [
            "bob@test.onion",
        ]
    )

    assert (
        item.message.headers.get(
            "Subject"
        )
        == "Queue Test"
    )

    assert item.message.body == "Hello Queue"