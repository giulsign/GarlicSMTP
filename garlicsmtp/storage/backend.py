from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime

from garlicsmtp.models import MailMessage
from garlicsmtp.storage.entry import MessageEntry


class MessageStoreBackend(ABC):

    @abstractmethod
    def save(
        self,
        mailbox: str,
        message: MailMessage,
    ) -> str:
        """Store a message and return its identifier."""
        raise NotImplementedError

    @abstractmethod
    def list_messages(
        self,
        mailbox: str,
    ) -> list[str]:
        """Return message identifiers for a mailbox."""
        raise NotImplementedError

    @abstractmethod
    def get(
        self,
        mailbox: str,
        message_id: str,
    ) -> MailMessage | None:
        """Return a stored message, if present."""
        raise NotImplementedError
    

    @abstractmethod
    def list_mailboxes(self) -> list[str]:
        """Return all mailbox names."""
        raise NotImplementedError
    

    @abstractmethod
    def create_mailbox(
        self,
        mailbox: str,
    ) -> bool:
        """
        Create an empty mailbox.

        Return False when the mailbox already exists.
        """
        raise NotImplementedError

    @abstractmethod
    def delete_mailbox(
        self,
        mailbox: str,
    ) -> bool:
        """
        Delete a mailbox and all its messages.

        Return False when the mailbox does not exist.
        """
        raise NotImplementedError

    @abstractmethod
    def rename_mailbox(
        self,
        source: str,
        destination: str,
    ) -> bool:
        """
        Rename a mailbox.

        Return False when the source does not exist or
        the destination already exists.
        """
        raise NotImplementedError

    @abstractmethod
    def subscribe_mailbox(
        self,
        mailbox: str,
    ) -> bool:
        """
        Subscribe to an existing mailbox.

        Return False when the mailbox does not exist.
        """
        raise NotImplementedError

    @abstractmethod
    def unsubscribe_mailbox(
        self,
        mailbox: str,
    ) -> bool:
        """
        Remove a mailbox subscription.

        Return False when the mailbox is not subscribed.
        """
        raise NotImplementedError

    @abstractmethod
    def list_subscribed_mailboxes(
        self,
    ) -> list[str]:
        """Return subscribed mailbox names."""
        raise NotImplementedError

    @abstractmethod
    def count(self, mailbox: str) -> int:
        """Return the number of messages in a mailbox."""
        raise NotImplementedError
    
    @abstractmethod
    def save_entry(
        self,
        mailbox: str,
        message: MailMessage,
    ) -> MessageEntry:
        raise NotImplementedError
    
    @abstractmethod
    def append_entry(
        self,
        mailbox: str,
        message: MailMessage,
        flags: set[str],
        internal_date: datetime,
    ) -> MessageEntry:
        """Append a message with explicit IMAP metadata."""
        raise NotImplementedError


    @abstractmethod
    def get_entry(
        self,
        mailbox: str,
        message_id: str,
    ) -> MessageEntry | None:
        raise NotImplementedError


    @abstractmethod
    def list_entries(
        self,
        mailbox: str,
    ) -> list[MessageEntry]:
        raise NotImplementedError
    
    @abstractmethod
    def set_flags(
        self,
        mailbox: str,
        message_id: str,
        flags: set[str],
    ) -> bool:
        raise NotImplementedError
    

    @abstractmethod
    def add_flags(
        self,
        mailbox: str,
        message_id: str,
        flags: set[str],
    ) -> bool:
        raise NotImplementedError


    @abstractmethod
    def remove_flags(
        self,
        mailbox: str,
        message_id: str,
        flags: set[str],
    ) -> bool:
        raise NotImplementedError
    
    @abstractmethod
    def copy_entry(
        self,
        source_mailbox: str,
        message_id: str,
        destination_mailbox: str,
    ) -> MessageEntry | None:
        """Copy an entry and assign a new destination UID."""
        raise NotImplementedError

    @abstractmethod
    def delete_entry(
        self,
        mailbox: str,
        message_id: str,
    ) -> bool:
        raise NotImplementedError