from dataclasses import dataclass

from garlicsmtp.storage.entry import MessageEntry
from garlicsmtp.storage.store import MessageStore
from enum import Enum
from datetime import UTC, datetime
from garlicsmtp.models import MailMessage


class StoreOperation(Enum):
    SET = "SET"
    ADD = "ADD"
    REMOVE = "REMOVE"

@dataclass(slots=True)
class MailboxView:

    name: str

    store: MessageStore

    def list_entries(
        self,
    ) -> list[MessageEntry]:
        return self.store.list_entries(
            self.name
        )

    def count(
        self,
    ) -> int:
        return self.store.count(
            self.name
        )

    def get_by_id(
        self,
        message_id: str,
    ) -> MessageEntry | None:
        return self.store.get_entry(
            self.name,
            message_id,
        )


    def get_by_uid_with_sequence(
        self,
        uid: int,
    ) -> tuple[int, MessageEntry] | None:
        for sequence_number, entry in enumerate(
            self.list_entries(),
            start=1,
        ):
            if entry.uid == uid:
                return sequence_number, entry

        return None


    def get_by_uid(
        self,
        uid: int,
    ) -> MessageEntry | None:
        result = self.get_by_uid_with_sequence(
            uid
        )

        if result is None:
            return None

        _, entry = result

        return entry


    def get_sequence_number(
        self,
        uid: int,
    ) -> int | None:
        result = self.get_by_uid_with_sequence(
            uid
        )

        if result is None:
            return None

        sequence_number, _ = result

        return sequence_number

    def next_uid(
        self,
    ) -> int:
        return max(
            (
                entry.uid
                for entry in self.list_entries()
            ),
            default=0,
        ) + 1

    def uid_validity(
        self,
    ) -> int:
        return 1

    def highest_modseq(
        self,
    ) -> int:
        return 1

    def first_unseen_uid(
        self,
    ) -> int | None:
        for entry in self.list_entries():
            if "\\Seen" not in entry.flags:
                return entry.uid

        return None
    
    def unseen_count(
        self,
    ) -> int:
        return sum(
            1
            for entry in self.list_entries()
            if "\\Seen" not in entry.flags
        )

    def set_flags(
        self,
        message_id: str,
        flags: set[str],
    ) -> bool:
        return self.store.set_flags(
            self.name,
            message_id,
            flags,
        )

    def add_flags(
        self,
        message_id: str,
        flags: set[str],
    ) -> bool:
        return self.store.add_flags(
            self.name,
            message_id,
            flags,
        )

    def remove_flags(
        self,
        message_id: str,
        flags: set[str],
    ) -> bool:
        return self.store.remove_flags(
            self.name,
            message_id,
            flags,
        )
    

    def delete(
        self,
        message_id: str,
    ) -> bool:
        return self.store.delete_entry(
            self.name,
            message_id,
        )
    

    def expunge_deleted(
        self,
    ) -> list[int]:
        expunged_sequence_numbers = []
        deleted_count = 0

        for original_sequence_number, entry in enumerate(
            self.list_entries(),
            start=1,
        ):
            if "\\Deleted" not in entry.flags:
                continue

            sequence_number = (
                original_sequence_number
                - deleted_count
            )

            if self.delete(entry.id):
                expunged_sequence_numbers.append(
                    sequence_number
                )
                deleted_count += 1

        return expunged_sequence_numbers
    

    def fetch_by_uid(
        self,
        uid: int,
    ) -> tuple[int, MessageEntry] | None:
        return self.get_by_uid_with_sequence(uid)


    def store_flags(
        self,
        uid: int,
        operation: StoreOperation,
        flags: set[str],
    ) -> tuple[int, MessageEntry] | None:
        result = self.get_by_uid_with_sequence(
            uid
        )

        if result is None:
            return None

        sequence_number, entry = result

        if operation is StoreOperation.SET:
            updated = self.set_flags(
                entry.id,
                flags,
            )

        elif operation is StoreOperation.ADD:
            updated = self.add_flags(
                entry.id,
                flags,
            )

        elif operation is StoreOperation.REMOVE:
            updated = self.remove_flags(
                entry.id,
                flags,
            )

        else:
            raise ValueError(
                f"Unsupported store operation: "
                f"{operation}"
            )

        if not updated:
            return None

        refreshed = self.get_by_id(
            entry.id
        )

        if refreshed is None:
            return None

        return (
            sequence_number,
            refreshed,
        )
    
    def append_message(
        self,
        message: MailMessage,
        flags: set[str] | None = None,
        internal_date: datetime | None = None,
    ) -> MessageEntry:
        effective_flags = (
            set(flags)
            if flags is not None
            else set()
        )

        effective_date = (
            internal_date
            if internal_date is not None
            else datetime.now(UTC)
        )

        return self.store.append_entry(
            self.name,
            message,
            effective_flags,
            effective_date,
        )


    def copy_by_uid(
        self,
        uid: int,
        destination_mailbox: str,
    ) -> tuple[int, int] | None:
        result = self.get_by_uid_with_sequence(
            uid
        )

        if result is None:
            return None

        _, source = result

        copied = self.store.copy_entry(
            self.name,
            source.id,
            destination_mailbox,
        )

        if copied is None:
            return None

        return (
            source.uid,
            copied.uid,
        )

    def move_by_uid(
        self,
        uid: int,
        destination_mailbox: str,
    ) -> tuple[int, int, int] | None:
        result = self.get_by_uid_with_sequence(
            uid
        )

        if result is None:
            return None

        sequence_number, source = result

        copied = self.store.copy_entry(
            self.name,
            source.id,
            destination_mailbox,
        )

        if copied is None:
            return None

        deleted = self.delete(
            source.id
        )

        if not deleted:
            self.store.delete_entry(
                destination_mailbox,
                copied.id,
            )

            return None

        return (
            source.uid,
            copied.uid,
            sequence_number,
        )
    

     