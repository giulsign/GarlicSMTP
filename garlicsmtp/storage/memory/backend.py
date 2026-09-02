# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from collections import defaultdict
from uuid import uuid4
from copy import deepcopy

from garlicsmtp.models import MailMessage
from garlicsmtp.storage.backend import MessageStoreBackend
from datetime import UTC, datetime
from uuid import uuid4

from garlicsmtp.storage.entry import MessageEntry
from garlicsmtp.storage.entry import VerificationStatus


class MemoryMessageStoreBackend(
    MessageStoreBackend
):

    def __init__(self):
        self._mailboxes = defaultdict(dict)
        self._next_uids = defaultdict(
            lambda: 1
        )
        self._mailbox_names = set()
        self._subscriptions: set[str] = set()
        self._uid_validities: dict[str, int] = {}
        self._next_uid_validity = 1

    def save(
        self,
        mailbox: str,
        message: MailMessage,
    ) -> str:
        return self.save_entry(
            mailbox,
            message,
        ).id
    
    def save_entry(
        self,
        mailbox: str,
        message: MailMessage,
        verification_status: VerificationStatus = (
            VerificationStatus.UNSIGNED
        ),
    ) -> MessageEntry:
        self._mailbox_names.add(
            mailbox
        )
        self._ensure_uid_validity(
            mailbox
        )

        message_id = str(uuid4())
        uid = self._next_uids[mailbox]

        self._next_uids[mailbox] += 1

        entry = MessageEntry(
            id=message_id,
            mailbox=mailbox,
            uid=uid,
            message=message,
            internal_date=datetime.now(UTC),
            verification_status=verification_status,
        )

        self._mailboxes[mailbox][
            message_id
        ] = entry

        return entry
    
    def append_entry(
        self,   
        mailbox: str,
        message: MailMessage,
        flags: set[str],
        internal_date: datetime,
    ) -> MessageEntry:
        self._mailbox_names.add(
            mailbox
        )
        self._ensure_uid_validity(
            mailbox
        )

        message_id = str(uuid4())
        uid = self._next_uids[mailbox]

        self._next_uids[mailbox] += 1

        entry = MessageEntry(
            id=message_id,
            mailbox=mailbox,
            uid=uid,
            message=message,
            internal_date=internal_date,
            flags=set(flags),
        )

        self._mailboxes[
            mailbox
        ][message_id] = entry

        return entry

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
        entry = self.get_entry(
            mailbox,
            message_id,
        )

        if entry is None:
            return None

        return entry.message
    

    def get_entry(
        self,
        mailbox: str,
        message_id: str,
    ) -> MessageEntry | None:
        return self._mailboxes[
            mailbox
        ].get(message_id)
    
    
    def list_entries(
        self,
        mailbox: str,
    ) -> list[MessageEntry]:
        return sorted(
            self._mailboxes[
                mailbox
            ].values(),
            key=lambda entry: entry.uid,
        )
    
    
    def list_mailboxes(self) -> list[str]:
        return sorted(
            self._mailbox_names
        )
    
    def create_mailbox(
        self,
        mailbox: str,
    ) -> bool:
        if mailbox in self._mailbox_names:
            return False

        self._mailbox_names.add(
            mailbox
        )

        self._ensure_uid_validity(
            mailbox
        )

        return True

    def delete_mailbox(
        self,
        mailbox: str,   
    ) -> bool:
        if mailbox not in self._mailbox_names:
            return False

        self._mailbox_names.remove(
            mailbox
        )

        self._mailboxes.pop(
            mailbox,
            None,
        )


        self._next_uids.pop(
            mailbox,
            None,
        )

        self._subscriptions.discard(
            mailbox
        )

        self._uid_validities.pop(
            mailbox,
            None,
        )

        return True

    def rename_mailbox(
        self,
        source: str,
        destination: str,
    ) -> bool:
        if source not in self._mailbox_names:
            return False

        if destination in self._mailbox_names:
            return False

        self._mailbox_names.remove(
            source
        )

        self._mailbox_names.add(
            destination
        )

        if source in self._mailboxes:
            self._mailboxes[destination] = (
                self._mailboxes.pop(source)
            )

        if source in self._next_uids:
            self._next_uids[destination] = (
                self._next_uids.pop(source)
            )

        if source in self._subscriptions:
            self._subscriptions.remove(
                source
            )

            self._subscriptions.add(
                destination
            )

        if source in self._uid_validities:
            self._uid_validities[destination] = (
                self._uid_validities.pop(source)
            )

        return True

    def subscribe_mailbox(
        self,
        mailbox: str,
    ) -> bool:
        if mailbox not in self._mailbox_names:
            return False

        self._subscriptions.add(
            mailbox
        )

        return True

    def unsubscribe_mailbox(
        self,
        mailbox: str,
    ) -> bool:
        if mailbox not in self._subscriptions:
            return False

        self._subscriptions.remove(
            mailbox
        )

        return True

    def list_subscribed_mailboxes(
        self,
    ) -> list[str]:
        return sorted(
            self._subscriptions
        )

    def count(self, mailbox: str) -> int:
        return len(
            self._mailboxes[mailbox]
        )
    
    def set_flags(
        self,
        mailbox: str,
        message_id: str,
        flags: set[str],
    ) -> bool:
        entry = self.get_entry(
            mailbox,
            message_id,
        )

        if entry is None:
            return False

        entry.flags = set(flags)

        return True
    

    def add_flags(
        self,
        mailbox: str,
        message_id: str,
        flags: set[str],
    ) -> bool:
        entry = self.get_entry(
            mailbox,
            message_id,
        )

        if entry is None:
            return False

        entry.flags.update(flags)

        return True


    def remove_flags(
        self,
        mailbox: str,
        message_id: str,
        flags: set[str],
    ) -> bool:
        entry = self.get_entry(
            mailbox,
            message_id,
        )

        if entry is None:
            return False

        entry.flags.difference_update(flags)

        return True

    def copy_entry(
        self,
        source_mailbox: str,
        message_id: str,
        destination_mailbox: str,
    ) -> MessageEntry | None:
        source = self.get_entry(
            source_mailbox,
            message_id,
        )

        if source is None:
            return None
                
        self._mailbox_names.add(
            destination_mailbox
        )

        copied_id = str(uuid4())
        copied_uid = self._next_uids[
            destination_mailbox
        ]

        self._next_uids[
            destination_mailbox
        ] += 1

        copied = MessageEntry(
            id=copied_id,
            mailbox=destination_mailbox,
            uid=copied_uid,
            message=deepcopy(source.message),
            internal_date=source.internal_date,
            flags=set(source.flags),
        )

        self._mailboxes[
            destination_mailbox
        ][copied_id] = copied

        return copied

    def delete_entry(
        self,
        mailbox: str,
        message_id: str,
    ) -> bool:
        return (
            self._mailboxes[mailbox]
            .pop(message_id, None)
            is not None
        )

    def _ensure_uid_validity(
        self,
        mailbox: str,
    ) -> None:
        if mailbox in self._uid_validities:
            return

        self._uid_validities[mailbox] = (
            self._next_uid_validity
        )

        self._next_uid_validity += 1

    def get_uid_validity(
        self,
        mailbox: str,
    ) -> int:
        self._ensure_uid_validity(
            mailbox
        )

        return self._uid_validities[
            mailbox
        ]