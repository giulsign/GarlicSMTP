from garlicsmtp.application.mail_composer import (
    MailComposerService,
)
import pytest


class FakeQueue:

    def __init__(self):
        self.items = []

    def enqueue(
        self,
        item,
    ):
        self.items.append(
            item
        )

        return True


def test_mail_composer_queues_message():
    queue = FakeQueue()

    composer = MailComposerService(
        queue
    )

    result = composer.send(
        sender="alice@sender.onion",
        recipient="bob@receiver.onion",
        subject="Hello",
        body="Hello from GarlicSMTP",
    )

    assert result is True

    assert len(
        queue.items
    ) == 1

    message = (
        queue.items[0]
        .message
    )

    assert (
        message.envelope.sender
        == "alice@sender.onion"
    )

    assert (
        message.envelope.recipients
        == [
            "bob@receiver.onion",
        ]
    )

    assert (
        message.headers.get(
            "Subject"
        )
        == "Hello"
    )

    assert (
        message.body
        == "Hello from GarlicSMTP"
    )


def test_mail_composer_rejects_empty_sender():
    composer = MailComposerService(
        FakeQueue()
    )

    with pytest.raises(
        ValueError
    ):
        composer.send(
            sender=" ",
            recipient="bob@receiver.onion",
            subject="Hello",
            body="Test",
        )


def test_mail_composer_rejects_empty_recipient():
    composer = MailComposerService(
        FakeQueue()
    )

    with pytest.raises(
        ValueError
    ):
        composer.send(
            sender="alice@sender.onion",
            recipient=" ",
            subject="Hello",
            body="Test",
        )
