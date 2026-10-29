# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import pytest

from garlicsmtp.network.socks5.exceptions import Socks5HandshakeError

from garlicsmtp.network.socks5.connection import Socks5Connection


class FakeSocket:

    def __init__(self):
        self.sent = b""
        self.closed = False

    def sendall(self, data):
        self.sent += data

    def recv(self, size):
        return b"OK"

    def close(self):
        self.closed = True


def test_socks5_connection_send_receive_close():

    conn = Socks5Connection()
    conn.socket = FakeSocket()

    conn.send(b"HELLO")

    assert conn.socket.sent == b"HELLO"

    assert conn.receive() == b"OK"

    sock = conn.socket

    conn.close()

    assert sock.closed is True
    assert conn.socket is None


def test_socks5_handshake():

    conn = Socks5Connection()
    conn.socket = FakeSocket()
    conn.socket.response = b"\x05\x00"

    def recv(size):
        return conn.socket.response

    conn.socket.recv = recv

    conn.handshake()

    assert conn.socket.sent == b"\x05\x01\x00"





def test_socks5_handshake_failure():

    conn = Socks5Connection()
    conn.socket = FakeSocket()
    conn.socket.response = b"\x05\xff"

    def recv(size):
        return conn.socket.response

    conn.socket.recv = recv

    with pytest.raises(Socks5HandshakeError):
        conn.handshake()


def test_socks5_connection_closes_previous_socket_on_reconnect(
    monkeypatch,
):
    first_socket = FakeSocket()
    second_socket = FakeSocket()
    sockets = iter([first_socket, second_socket])

    monkeypatch.setattr(
        "garlicsmtp.network.socks5.connection.socket.create_connection",
        lambda *args, **kwargs: next(sockets),
    )

    conn = Socks5Connection()

    conn.connect()
    assert conn.socket is first_socket

    conn.connect()

    assert first_socket.closed is True
    assert conn.socket is second_socket

    conn.close()
    assert second_socket.closed is True
    assert conn.socket is None