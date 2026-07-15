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