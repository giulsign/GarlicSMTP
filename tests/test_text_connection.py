# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.network.text.connection import TextConnection


class FakeSocket:
    def __init__(
        self,
        incoming: bytes | None = None,
    ):
        if incoming is None:
            incoming = (
                b"220 smtp.example.com\r\n"
            )

        self.incoming = incoming
        self.sent = b""
        self.closed = False

    def recv(
        self,
        size: int,
    ) -> bytes:
        if not self.incoming:
            return b""

        chunk = self.incoming[:size]

        self.incoming = self.incoming[
            size:
        ]

        return chunk

    def sendall(
        self,
        data: bytes,
    ) -> None:
        self.sent += data

    def close(
        self,
    ) -> None:
        self.closed = True


def test_connection_send_receive():

    conn = TextConnection()

    conn.socket = FakeSocket()

    conn.send("EHLO test\r\n")

    assert conn.socket.sent == b"EHLO test\r\n"

    assert conn.receive() == "220 smtp.example.com\r\n"


def test_text_connection_sends_bytes():

    connection = TextConnection()

    connection.socket = FakeSocket()

    connection.send_bytes(
        b"binary-data"
    )

    assert connection.socket.sent == b"binary-data"


def test_text_connection_receives_exact_bytes():
    connection = TextConnection()

    connection.socket = FakeSocket(
        b"literal-dataremaining"
    )

    assert connection.receive_bytes(
        12
    ) == b"literal-data"

    assert connection.receive_bytes(
        9
    ) == b"remaining"


def test_text_connection_receives_bytes_after_line():
    connection = TextConnection()

    connection.socket = FakeSocket(
        (
            b"A100 APPEND archive {4}\r\n"
            b"mail"
            b"A101 NOOP\r\n"
        )
    )

    assert connection.receive_line() == (
        "A100 APPEND archive {4}"
    )

    assert connection.receive_bytes(
        4
    ) == b"mail"

    assert connection.receive_line() == (
        "A101 NOOP"
    )


def test_text_connection_receives_zero_bytes():
    connection = TextConnection()

    connection.socket = FakeSocket(
        b"remaining"
    )

    assert connection.receive_bytes(
        0
    ) == b""

    assert connection.receive_bytes(
        9
    ) == b"remaining"


def test_text_connection_returns_none_on_incomplete_bytes():
    connection = TextConnection()

    connection.socket = FakeSocket(
        b"short"
    )

    assert connection.receive_bytes(
        10
    ) is None