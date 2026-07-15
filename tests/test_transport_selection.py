from garlicsmtp.queue.factory import QueueFactory
from garlicsmtp.transport.dummy import DummyTransport
from garlicsmtp.transport.manager import TransportManager
from garlicsmtp.transport.onion.dummy import DummyOnionTransport


def test_onion_is_default_for_onion_recipient(message):

    item = QueueFactory.create(message)

    onion = DummyOnionTransport()
    smtp = DummyTransport()

    manager = TransportManager(
        default_transport=onion,
        smtp_transport=smtp,
    )

    assert manager.deliver(item) is True
    assert onion.delivered == [item]
    assert smtp.delivered == []


def test_smtp_is_used_for_non_onion_recipient(message):

    message.envelope.recipients = ["bob@example.com"]

    item = QueueFactory.create(message)

    onion = DummyOnionTransport()
    smtp = DummyTransport()

    manager = TransportManager(
        default_transport=onion,
        smtp_transport=smtp,
    )

    assert manager.deliver(item) is True
    assert smtp.delivered == [item]
    assert onion.delivered == []