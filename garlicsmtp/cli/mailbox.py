from __future__ import annotations

from garlicsmtp.storage.sqlite import (
    SQLiteMessageStoreBackend,
)
from garlicsmtp.storage.store import MessageStore


def build_mailbox_store(
    database_path: str,
) -> MessageStore:
    backend = SQLiteMessageStoreBackend(
        database_path
    )

    return MessageStore(
        backend=backend,
    )


def format_flags(
    flags: set[str],
) -> str:
    if not flags:
        return "-"

    return ", ".join(
        sorted(flags)
    )


def list_mailboxes(
    database_path: str,
) -> int:
    store = build_mailbox_store(
        database_path
    )

    try:
        mailboxes = store.list_mailboxes()

        print(
            f"Mailbox database: {database_path}"
        )
        print()

        if not mailboxes:
            print("No mailboxes found.")
            return 0

        print("Mailboxes")
        print()

        for mailbox in mailboxes:
            count = store.count(
                mailbox
            )

            print(mailbox)
            print(
                f"  Messages: {count}"
            )
            print()

        return 0

    finally:
        store.backend.close()


def list_messages(
    database_path: str,
    mailbox: str,
) -> int:
    store = build_mailbox_store(
        database_path
    )

    try:
        entries = store.list_entries(
            mailbox
        )

        print(f"Mailbox: {mailbox}")
        print()

        if not entries:
            print("No messages found.")
            return 0

        for entry in entries:
            message = entry.message

            subject = message.headers.fields.get(
                "Subject",
                "(no subject)",
            )

            print(f"UID {entry.uid}")
            print(
                f"  ID: {entry.id}"
            )
            print(
                f"  From: "
                f"{message.envelope.sender}"
            )
            print(
                f"  Subject: {subject}"
            )
            print(
                f"  Flags: "
                f"{format_flags(entry.flags)}"
            )
            print(
                "  Internal-Date: "
                f"{entry.internal_date.isoformat()}"
            )
            print()

        return 0

    finally:
        store.backend.close()


def show_message(
    database_path: str,
    mailbox: str,
    message_reference: str,
) -> int:
    store = build_mailbox_store(
        database_path
    )

    try:
        message_id = resolve_message_id(
            store=store,
            mailbox=mailbox,
            reference=message_reference,
        )

        if message_id is None:
            print("Message not found.")
            return 1

        entry = store.get_entry(
            mailbox,
            message_id,
        )

        if entry is None:
            print("Message not found.")
            return 1

        message = entry.message

        subject = message.headers.fields.get(
            "Subject",
            "(no subject)",
        )

        print(f"Message ID: {entry.id}")
        print(f"UID: {entry.uid}")
        print(
            f"Flags: "
            f"{format_flags(entry.flags)}"
        )
        print(
            "Internal-Date: "
            f"{entry.internal_date.isoformat()}"
        )
        print()
        print(
            f"From: {message.envelope.sender}"
        )
        print(
            "To: "
            + ", ".join(
                message.envelope.recipients
            )
        )
        print(f"Subject: {subject}")

        for name, value in (
            message.headers.fields.items()
        ):
            if name.lower() == "subject":
                continue

            if isinstance(value, list):
                for entry_value in value:
                    print(
                        f"{name}: {entry_value}"
                    )
            else:
                print(f"{name}: {value}")

        print()
        print(message.body or "")

        return 0

    finally:
        store.backend.close()


def resolve_message_id(
    store: MessageStore,
    mailbox: str,
    reference: str,
) -> str | None:
    entries = store.list_entries(
        mailbox
    )

    try:
        uid = int(reference)
    except ValueError:
        for entry in entries:
            if entry.id == reference:
                return entry.id

        return None

    if uid < 1:
        return None

    for entry in entries:
        if entry.uid == uid:
            return entry.id

    return None


def update_flags(
    database_path: str,
    mailbox: str,
    message_reference: str,
    operation: str,
    flags: set[str],
) -> int:
    store = build_mailbox_store(
        database_path
    )

    try:
        message_id = resolve_message_id(
            store=store,
            mailbox=mailbox,
            reference=message_reference,
        )

        if message_id is None:
            print("Message not found.")
            return 1

        entry = store.get_entry(
            mailbox,
            message_id,
        )

        if entry is None:
            print("Message not found.")
            return 1

        if operation == "add":
            updated = store.add_flags(
                mailbox,
                message_id,
                flags,
            )

        elif operation == "remove":
            updated = store.remove_flags(
                mailbox,
                message_id,
                flags,
            )

        elif operation == "set":
            updated = store.set_flags(
                mailbox,
                message_id,
                flags,
            )

        else:
            print(
                f"Unsupported flag operation: "
                f"{operation}"
            )
            return 2
        
        updated_entry = store.get_entry(
            mailbox,
            message_id,
        )

        if updated_entry is None:
            print("Message not found.")
            return 1

        if not updated:
            print(
                "Unable to update message flags."
            )
            return 1

        print(
            f"UID {updated_entry.uid} flags: "
            f"{format_flags(updated_entry.flags)}"
        )

        return 0

    finally:
        store.backend.close()