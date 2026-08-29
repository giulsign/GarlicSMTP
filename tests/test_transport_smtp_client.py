# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.transport.smtp.client import SMTPClient


class FakeProtocol:

    def __init__(self):
        self.calls = []

    def greeting(self):
        self.calls.append(
            ("greeting",)
        )

    def ehlo(self, hostname):
        self.calls.append(
            ("ehlo", hostname)
        )

    def mail_from(self, sender):
        self.calls.append(
            ("mail_from", sender)
        )

    def rcpt_to(self, recipient):
        self.calls.append(
            ("rcpt_to", recipient)
        )

    def data(self, content):
        self.calls.append(
            ("data", content)
        )

    def quit(self):
        self.calls.append(
            ("quit",)
        )


def test_smtp_client_delivers_message(message):

    client = SMTPClient.__new__(
        SMTPClient
    )
    

    client.hostname = "garlicsmtp.local"
    client.protocol = FakeProtocol()

    message.headers.fields[
        "Subject"
    ] = "Test"

    message.body = "Hello"

    assert client.deliver(message) is True

    assert client.protocol.calls == [
        ("greeting",),
        (
            "ehlo",
            "garlicsmtp.local",
        ),
        (
            "mail_from",
            "alice@test.onion",
        ),
        (
            "rcpt_to",
            "bob@test.onion",
        ),
        (
            "data",
            "Subject: Test\r\n\r\nHello",
        ),
        ("quit",),
    ]


from garlicsmtp.models import Envelope, MailHeaders, MailMessage
from garlicsmtp.transport.smtp.client import SMTPClient


def test_smtp_client_serialization_does_not_add_headers():
    headers = MailHeaders()
    headers.add(
        "Subject",
        "Hello",
    )

    message = MailMessage(
        envelope=Envelope(
            sender="alice@sender.onion",
            recipients=[
                "bob@receiver.onion",
            ],
        ),
        headers=headers,
        body="Hello",
    )

    serialized = SMTPClient.serialize_message(
        message
    )

    header_block = serialized.split(
        "\r\n\r\n",
        1,
    )[0]

    assert "Subject: Hello" in header_block
    assert "Date:" not in header_block
    assert "Message-ID:" not in header_block
    assert "Received:" not in header_block
    assert "Return-Path:" not in header_block
    assert "X-Mailer:" not in header_block
    assert "User-Agent:" not in header_block