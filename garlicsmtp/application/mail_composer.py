from garlicsmtp.models import (
    Envelope,
    MailHeaders,
    MailMessage,
    Metadata,
)
from garlicsmtp.queue.factory import (
    QueueFactory,
)


class MailComposerService:

    def __init__(
        self,
        queue,
    ) -> None:
        self.queue = queue

    def send(
        self,
        *,
        sender: str,
        recipient: str,
        subject: str,
        body: str,
    ) -> bool:
        sender = sender.strip()
        recipient = recipient.strip()

        if not sender:
            raise ValueError(
                "sender cannot be empty"
            )

        if not recipient:
            raise ValueError(
                "recipient cannot be empty"
            )

        headers = MailHeaders()

        if subject:
            headers.add(
                "Subject",
                subject,
            )

        message = MailMessage(
            envelope=Envelope(
                sender=sender,
                recipients=[
                    recipient,
                ],
            ),
            headers=headers,
            metadata=Metadata(),
            body=body,
        )

        item = QueueFactory.create(
            message
        )

        return bool(
            self.queue.enqueue(
                item
            )
        )
