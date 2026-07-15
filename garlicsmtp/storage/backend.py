from __future__ import annotations
from abc import ABC, abstractmethod

from garlicsmtp.models import MailMessage


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
    def count(self, mailbox: str) -> int:
        """Return the number of messages in a mailbox."""
        raise NotImplementedError