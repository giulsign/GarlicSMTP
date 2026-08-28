# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from datetime import datetime
from typing import TYPE_CHECKING

from garlicsmtp.models import MailMessage
from garlicsmtp.storage.backend import (
    MessageStoreBackend,
)
from garlicsmtp.storage.entry import MessageEntry
from garlicsmtp.storage.event_sink import (
    StoreEventSink,
)
from garlicsmtp.storage.memory.backend import (
    MemoryMessageStoreBackend,
)
from garlicsmtp.storage.null_event_sink import (
    NullStoreEventSink,
)


class MessageStore:

    def __init__(
        self,
        backend: MessageStoreBackend | None = None,
        event_sink: StoreEventSink | None = None,
    ):
        self.backend = (
            backend
            or MemoryMessageStoreBackend()
        )

        self.event_sink = (
            event_sink
            or NullStoreEventSink()
        )

    def save(
        self,
        mailbox: str,
        message: MailMessage,
    ) -> str:
        return self.save_entry(
            mailbox,
            message,
        ).id

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
        entry = self.backend.save_entry(
            mailbox,
            message,
        )

        self.event_sink.message_added(
            mailbox
        )

        return entry
    
    def append_entry(   
        self,
        mailbox: str,
        message: MailMessage,
        flags: set[str],
        internal_date: datetime,
    ) -> MessageEntry:
        entry = self.backend.append_entry(
            mailbox,
            message,
            flags,
            internal_date,
        )

        self.event_sink.message_added(
            mailbox
        )

        return entry


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
        updated = self.backend.set_flags(
            mailbox,
            message_id,
            flags,
        )

        if updated:
            self.event_sink.flags_changed(
                mailbox
            )

        return updated
    

    def add_flags(
        self,
        mailbox: str,
        message_id: str,
        flags: set[str],
    ) -> bool:
        updated = self.backend.add_flags(
            mailbox,
            message_id,
            flags,
        )

        if updated:
            self.event_sink.flags_changed(
                mailbox
            )

        return updated


    def remove_flags(
        self,
        mailbox: str,
        message_id: str,
        flags: set[str],
    ) -> bool:
        updated = self.backend.remove_flags(
            mailbox,
            message_id,
            flags,
        )

        if updated:
            self.event_sink.flags_changed(
                mailbox
            )

        return updated
    

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
        copied = self.backend.copy_entry(
            source_mailbox,
            message_id,
            destination_mailbox,
        )

        if copied is None:
            return None

        self.event_sink.message_added(
            destination_mailbox
        )

        return copied

    def delete_entry(
        self,
        mailbox: str,
        message_id: str,
    ) -> bool:
        return self.backend.delete_entry(
            mailbox,
            message_id,
        )