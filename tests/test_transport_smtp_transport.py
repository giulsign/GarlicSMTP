# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.queue.factory import QueueFactory
from garlicsmtp.transport.dns.records import MXRecord
from garlicsmtp.transport.smtp.transport import SMTPTransport


class FakeResolver:

    def lookup_mx(self, domain):
        assert domain == "test.onion"

        return [
            MXRecord(
                priority=10,
                exchange="mail.test.onion",
            )
        ]


class FakeConnection:

    connected = []
    sent = []

    def __init__(self):
        self.closed = False

        self.replies = [
            "220 mail.test.onion ready\r\n",
            "250 EHLO OK\r\n",
            "250 MAIL OK\r\n",
            "250 RCPT OK\r\n",
            "354 End data\r\n",
            "250 Message accepted\r\n",
            "221 Bye\r\n",
        ]

    def connect(
        self,
        host,
        port=25,
    ):
        self.connected.append(
            (host, port)
        )

    def send(self, text):
        self.sent.append(text)

    def receive_line(self):
        return self.replies.pop(0).rstrip(
            "\r\n"
        )

    def close(self):
        self.closed = True


def test_transport_connects_to_mx(message):

    FakeConnection.connected.clear()
    FakeConnection.sent.clear()

    transport = SMTPTransport()

    transport.resolver = FakeResolver()
    transport.connection_factory = FakeConnection

    result = transport.deliver(
        QueueFactory.create(message)
    )

    assert result is True

    assert FakeConnection.connected == [
        ("mail.test.onion", 25)
    ]

    assert FakeConnection.sent == [
        "EHLO [127.0.0.1]\r\n",
        "MAIL FROM:<alice@test.onion>\r\n",
        "RCPT TO:<bob@test.onion>\r\n",
        "DATA\r\n",
        f"{message.body}\r\n.\r\n",
        "QUIT\r\n",
    ]