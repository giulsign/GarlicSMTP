from garlicsmtp.queue.factory import QueueFactory
from garlicsmtp.transport.dummy import DummyTransport
from garlicsmtp.transport.manager import TransportManager
from garlicsmtp.transport.onion.transport import OnionTransport


class FakeConnection:

    def __init__(self):
        self.socket = object()
        self.closed = False

    def close(self):
        self.closed = True


class FakeSocksClient:

    def __init__(self):
        self.connection = FakeConnection()
        self.connected = []

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
        self.delivered.append(message)
        return True


def test_transport_manager_uses_real_onion_transport(message):

    host = "a" * 56 + ".onion"

    message.envelope.recipients = [
        f"bob@{host}"
    ]

    item = QueueFactory.create(message)

    socks = FakeSocksClient()
    smtp_client = FakeSMTPClient()

    onion = OnionTransport(
        socks_client=socks,
        smtp_client_factory=lambda _: smtp_client,
    )

    smtp = DummyTransport()

    manager = TransportManager(
        default_transport=onion,
        smtp_transport=smtp,
    )

    assert manager.deliver(item) is True

    assert socks.connected == [
        (host, 25)
    ]

    assert smtp_client.delivered == [
        message
    ]

    assert socks.connection.closed is True
    assert smtp.delivered == []