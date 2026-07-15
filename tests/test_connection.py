from garlicsmtp.smtp.connection import SMTPConnection


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