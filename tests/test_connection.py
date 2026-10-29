# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import pytest

from garlicsmtp.smtp.connection import SMTPConnection
from garlicsmtp.smtp.datareceiver import SMTPDataReceiver


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


def test_connection_send():
    sock = FakeSocket()

    conn = SMTPConnection(
        sock,
        ("127.0.0.1", 2525),
    )

    conn.send(b"hello")

    assert sock.sent == b"hello"


def test_connection_receive():
    sock = FakeSocket()

    sock.buffer.append(
        b"EHLO test.onion\r\n"
    )

    conn = SMTPConnection(
        sock,
        ("127.0.0.1", 2525),
    )

    assert conn.receive_line() == "EHLO test.onion"


def test_connection_ip():
    conn = SMTPConnection(
        FakeSocket(),
        ("10.0.0.1", 5000),
    )

    assert conn.ip == "10.0.0.1"
    assert conn.port == 5000


def test_connection_rejects_oversized_line():
    sock = FakeSocket()
    sock.buffer.append(b"A" * (64 * 1024 + 1))

    conn = SMTPConnection(
        sock,
        ("127.0.0.1", 2525),
    )

    with pytest.raises(
        ValueError,
        match="SMTP line too long",
    ):
        conn.receive_line()


def test_data_receiver_rejects_message_over_two_mib():
    receiver = SMTPDataReceiver()

    receiver.append("A" * (1024 * 1024))
    receiver.append("B" * (1024 * 1024 - 1))

    # Esattamente 2 MiB, incluso il separatore.
    assert len(receiver.body().encode("utf-8")) == 2_097_152

    with pytest.raises(
        ValueError,
        match="SMTP message too large",
    ):
        receiver.append("C")