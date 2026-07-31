from garlicsmtp.models import MailMessage
from garlicsmtp.storage.backend import (
    MessageStoreBackend,
)
from garlicsmtp.storage.memory.backend import (
    MemoryMessageStoreBackend,
)   
from garlicsmtp.storage.entry import MessageEntry
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from garlicsmtp.storage.mailbox import (
        MailboxView,
    )
from datetime import datetime


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
    
    def create_mailbox(
        self,
        mailbox: str,
    ) -> bool:
        return self.backend.create_mailbox( 
            mailbox
        )

    def delete_mailbox(
        self,
        mailbox: str,
    ) -> bool:
        return self.backend.delete_mailbox(
            mailbox
        )

    def rename_mailbox(
        self,
        source: str,
        destination: str,
    ) -> bool:
        return self.backend.rename_mailbox(
            source,
            destination,
        )

    def subscribe_mailbox(
        self,
        mailbox: str,
    ) -> bool:
        return self.backend.subscribe_mailbox(
            mailbox
        )

    def unsubscribe_mailbox(
        self,
        mailbox: str,
    ) -> bool:
        return self.backend.unsubscribe_mailbox(
            mailbox
        )

    def list_subscribed_mailboxes(
        self,
    ) -> list[str]:
        return self.backend.list_subscribed_mailboxes()

    def count(self, mailbox: str) -> int:
            return self.backend.count(
                mailbox
            )

    def get_uid_validity(
        self,
        mailbox: str,
    ) -> int:
        return self.backend.get_uid_validity(
            mailbox
        )
    

    def save_entry(
        self,
        mailbox: str,
        message: MailMessage,
    ) -> MessageEntry:
        return self.backend.save_entry(
            mailbox,
            message,
        )
    
    def append_entry(
        self,
        mailbox: str,
        message: MailMessage,
        flags: set[str],
        internal_date: datetime,
    ) -> MessageEntry:
        return self.backend.append_entry(
            mailbox,
            message,
            flags,
            internal_date,
        )


    def get_entry(
        self,
        mailbox: str,
        message_id: str,
    ) -> MessageEntry | None:
        return self.backend.get_entry(
            mailbox,
            message_id,
        )


    def list_entries(
        self,
        mailbox: str,
    ) -> list[MessageEntry]:
        return self.backend.list_entries(
            mailbox
        )
    

    def set_flags(
        self,
        mailbox: str,
        message_id: str,
        flags: set[str],
    ) -> bool:
        return self.backend.set_flags(
            mailbox,
            message_id,
            flags,
        )
    

    def add_flags(
        self,
        mailbox: str,
        message_id: str,
        flags: set[str],
    ) -> bool:
        return self.backend.add_flags(
            mailbox,
            message_id,
            flags,
        )


    def remove_flags(
        self,
        mailbox: str,
        message_id: str,
        flags: set[str],
    ) -> bool:
        return self.backend.remove_flags(
            mailbox,
            message_id,
            flags,
        )
    

    def open_mailbox(
        self,
        mailbox: str,
    ):
        from garlicsmtp.storage.mailbox import (
            MailboxView,
        )

        return MailboxView(
            name=mailbox,
            store=self,
        )    

    def copy_entry(
        self,
        source_mailbox: str,
        message_id: str,
        destination_mailbox: str,
    ) -> MessageEntry | None:
        return self.backend.copy_entry(
            source_mailbox,
            message_id,
            destination_mailbox,
        )

    def delete_entry(
        self,
        mailbox: str,
        message_id: str,
    ) -> bool:
        return self.backend.delete_entry(
            mailbox,
            message_id,
        )