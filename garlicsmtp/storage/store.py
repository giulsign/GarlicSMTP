from garlicsmtp.models import MailMessage
from garlicsmtp.storage.backend import (
    MessageStoreBackend,
)
from garlicsmtp.storage.memory.backend import (
    MemoryMessageStoreBackend,
)


class MessageStore:

    def __init__(
        self,
        backend: MessageStoreBackend | None = None,
    ):
        self.backend = (
            backend
            or MemoryMessageStoreBackend()
        )

    def save(
        self,
        mailbox: str,
        message: MailMessage,
    ) -> str:
        return self.backend.save(
            mailbox,
            message,
        )

    def list_messages(
        self,
        mailbox: str,
    ) -> list[str]:
        return self.backend.list_messages(
            mailbox,
        )

    def get(
        self,
        mailbox: str,
        message_id: str,
    ):
        return self.backend.get(
            mailbox,
            message_id,
        )
    

    def list_mailboxes(self) -> list[str]:
        return self.backend.list_mailboxes()


    def count(self, mailbox: str) -> int:
        return self.backend.count(
            mailbox
        )