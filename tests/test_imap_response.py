# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.imap import (
    IMAPLiteralResponse,
    IMAPReply,
)


class FakeConnection:

    def __init__(self):
        self.sent = []

    def send(
        self,
        text: str,
    ) -> None:
        self.sent.append(text)

    def send_bytes(
        self,
        data: bytes,
    ) -> None:
        self.sent.append(data)


def test_imap_reply_sends_serialized_line():

    connection = FakeConnection()

    response = IMAPReply.tagged(
        "A001",
        "OK",
        "completed",
    )

    response.send(
        connection
    )

    assert connection.sent == [
        "A001 OK completed\r\n"
    ]


def test_imap_literal_response_sends_three_parts():

    connection = FakeConnection()

    response = IMAPLiteralResponse(
        prefix="* 1 FETCH (BODY[]",
        content=b"Subject: Test\r\n\r\nHello",
    )

    response.send(
        connection
    )

    assert connection.sent == [
        "* 1 FETCH (BODY[] {22}\r\n",
        b"Subject: Test\r\n\r\nHello",
        "\r\n)\r\n",
    ]