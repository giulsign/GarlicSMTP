# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.transport.smtp.connection import SMTPConnection


class FakeSocket:

    def __init__(self):
        self.sent = b""

    def sendall(self, data):
        self.sent += data

    def recv(self, size):
        return b"220 smtp.example.com\r\n"

    def close(self):
        pass


def test_connection_send_receive():

    conn = SMTPConnection()

    conn.socket = FakeSocket()

    conn.send("EHLO test\r\n")

    assert conn.socket.sent == b"EHLO test\r\n"

    assert conn.receive() == "220 smtp.example.com\r\n"