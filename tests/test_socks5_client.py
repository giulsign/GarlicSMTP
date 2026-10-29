# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import pytest

from garlicsmtp.network.socks5.exceptions import (
    Socks5HandshakeError,
)
from garlicsmtp.network.socks5.client import Socks5Client



class FakeConnection:

    def __init__(self):
        self.connected = False
        self.handshaked = False
        self.sent = []

        self.reply = bytearray(
            b"\x05\x00\x00\x01"
            b"\x7f\x00\x00\x01"
            b"\x00\x19"
        )

    def connect(self):
        self.connected = True

    def handshake(self):
        self.handshaked = True

    def send(self, data):
        self.sent.append(data)

    def receive_exactly(self, size):
        data = bytes(
            self.reply[:size]
        )

        del self.reply[:size]

        return data


def test_socks5_client_connect():

    connection = FakeConnection()

    client = Socks5Client(connection)

    result = client.connect(
        "example.onion",
        25,
    )

    assert result is connection
    assert connection.connected is True
    assert connection.handshaked is True
    assert connection.reply == bytearray()


class FakeReplyConnection:

    def __init__(self):
        self.sent = []
        self.chunks = bytearray(
            b"\x05\x00\x00\x01"
            b"\x7f\x00\x00\x01"
            b"\x00\x19"
        )

    def connect(self):
        pass

    def handshake(self):
        pass

    def send(self, data):
        self.sent.append(data)

    def receive_exactly(self, size):
        result = bytes(
            self.chunks[:size]
        )

        del self.chunks[:size]

        return result

def test_socks5_client_reads_complete_connect_reply():

    connection = FakeReplyConnection()

    client = Socks5Client(
        connection=connection,
    )

    result = client.connect(
        "a" * 56 + ".onion",
        25,
    )

    assert result is connection
    assert connection.chunks == bytearray()


def test_socks5_client_closes_connection_on_handshake_failure():
    class FailingHandshakeConnection:
        def __init__(self):
            self.connected = False
            self.closed = False

        def connect(self):
            self.connected = True

        def handshake(self):
            raise Socks5HandshakeError(
                "SOCKS5 handshake rejected"
            )

        def close(self):
            self.closed = True

    connection = FailingHandshakeConnection()
    client = Socks5Client(connection=connection)

    with pytest.raises(
        Socks5HandshakeError,
        match="SOCKS5 handshake rejected",
    ):
        client.connect("example.onion", 25)

    assert connection.connected is True
    assert connection.closed is True