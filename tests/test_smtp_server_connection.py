from garlicsmtp.smtp.server import SMTPServer
from garlicsmtp.core.pipeline import Pipeline


class FakeSocket:
    def __init__(self):
        self.sent = b""
        self.buffer = [
            b"QUIT\r\n"
        ]

    def sendall(self, data: bytes):
        self.sent += data

    def recv(self, size):
        if self.buffer:
            return self.buffer.pop(0)
        return b""

    def close(self):
        pass
        

def test_smtp_server_handles_connection():
    server = SMTPServer(
        hostname="garlicsmtp.onion",
        pipeline=Pipeline(),
    )
    client = FakeSocket()

    server.handle_connection(
        client,
        ("127.0.0.1", 10000),
    )

    assert client.sent == (
        b"220 garlicsmtp.onion GarlicSMTP ready\r\n"
        b"221 Bye\r\n"
    )