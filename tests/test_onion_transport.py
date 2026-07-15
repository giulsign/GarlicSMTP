from garlicsmtp.queue.factory import QueueFactory
from garlicsmtp.transport.onion.transport import OnionTransport


class FakeConnection:

    def __init__(self):
        self.socket = object()
        self.closed = False

    def close(self):
        self.closed = True


class FakeSocksClient:

    def __init__(self):
        self.connected = []
        self.connection = FakeConnection()

    def connect(
        self,
        host,
        port,
    ):
        self.connected.append(
            (host, port)
        )

        return self.connection


class FakeSMTPClient:

    def __init__(self):
        self.delivered = []

    def deliver(self, message):
        self.delivered.append(
            message
        )

        return True


def test_onion_transport_connects_and_delivers(message):

    host = "a" * 56 + ".onion"

    message.envelope.recipients = [
        f"bob@{host}"
    ]

    item = QueueFactory.create(
        message
    )

    socks = FakeSocksClient()
    smtp = FakeSMTPClient()

    transport = OnionTransport(
        socks_client=socks,
        smtp_client_factory=(
            lambda connection: smtp
        ),
    )

    assert transport.deliver(item) is True

    assert socks.connected == [
        (host, 25)
    ]

    assert smtp.delivered == [
        message
    ]

    assert socks.connection.closed is True


class ScriptedSocket:

    def __init__(self):
        self.sent = bytearray()
        self.closed = False
        self.timeout = None

        self.responses = bytearray(
            b"220 mail.hidden ready\r\n"
            b"250 mail.hidden\r\n"
            b"250 sender accepted\r\n"
            b"250 recipient accepted\r\n"
            b"354 end with dot\r\n"
            b"250 message accepted\r\n"
            b"221 bye\r\n"
        )

    def settimeout(self, timeout):
        self.timeout = timeout

    def sendall(self, data):
        self.sent.extend(data)

    def recv(self, size):
        if not self.responses:
            return b""

        data = bytes(
            self.responses[:size]
        )

        del self.responses[:size]

        return data

    def close(self):
        self.closed = True


class ScriptedSocksConnection:

    def __init__(self):
        self.socket = ScriptedSocket()
        self.closed = False

    def close(self):
        self.socket.close()
        self.closed = True


class ScriptedSocksClient:

    def __init__(self):
        self.connection = ScriptedSocksConnection()
        self.connected = []

    def connect(self, host, port):
        self.connected.append(
            (host, port)
        )

        return self.connection
    

def test_onion_transport_runs_real_smtp_client(message):

    host = "a" * 56 + ".onion"

    message.envelope.sender = (
        "alice@sender.onion"
    )

    message.envelope.recipients = [
        f"bob@{host}"
    ]

    message.headers.fields[
        "Subject"
    ] = "Tor delivery test"

    message.body = "Hello over Tor"

    item = QueueFactory.create(
        message
    )

    socks = ScriptedSocksClient()

    transport = OnionTransport(
        socks_client=socks,
        hostname="sender.onion",
    )

    assert transport.deliver(item) is True

    assert socks.connected == [
        (host, 25)
    ]

    sent = bytes(
        socks.connection.socket.sent
    ).decode("utf-8")

    assert sent == (
        "EHLO sender.onion\r\n"
        "MAIL FROM:<alice@sender.onion>\r\n"
        f"RCPT TO:<bob@{host}>\r\n"
        "DATA\r\n"
        "Subject: Tor delivery test\r\n"
        "\r\n"
        "Hello over Tor\r\n"
        ".\r\n"
        "QUIT\r\n"
    )

    assert socks.connection.closed is True