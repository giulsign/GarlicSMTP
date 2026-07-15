from collections import defaultdict
from uuid import uuid4

from garlicsmtp.models import MailMessage
from garlicsmtp.storage.backend import MessageStoreBackend


class MemoryMessageStoreBackend(
    MessageStoreBackend
):

    def __init__(self):
        self._mailboxes = defaultdict(dict)

    def save(
        self,
        mailbox: str,
        message: MailMessage,
    ) -> str:
        message_id = str(uuid4())

        self._mailboxes[mailbox][
            message_id
        ] = message

        return message_id

    def list_messages(
        self,
        mailbox: str,
    ) -> list[str]:
        return list(
            self._mailboxes[mailbox].keys()
        )

    def get(
        self,
        mailbox: str,
        message_id: str,
    ) -> MailMessage | None:
        return self._mailboxes[
            mailbox
        ].get(message_id)
    
    def list_mailboxes(self) -> list[str]:
        return [
            mailbox
            for mailbox, messages
            in self._mailboxes.items()
            if messages
        ]


    def count(self, mailbox: str) -> int:
        return len(
            self._mailboxes[mailbox]
        )