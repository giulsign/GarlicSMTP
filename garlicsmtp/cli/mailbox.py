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
        message_ids = store.list_messages(
            mailbox
        )

        print(f"Mailbox: {mailbox}")
        print()

        if not message_ids:
            print("No messages found.")
            return 0

        for position, message_id in enumerate(
            message_ids,
            start=1,
        ):
            message = store.get(
                mailbox,
                message_id,
            )

            if message is None:
                continue

            subject = message.headers.fields.get(
                "Subject",
                "(no subject)",
            )

            print(f"{position}.")
            print(
                f"  ID: {message_id}"
            )
            print(
                f"  From: "
                f"{message.envelope.sender}"
            )
            print(
                f"  Subject: {subject}"
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
            print(
                "Message not found."
            )
            return 1

        message = store.get(
            mailbox,
            message_id,
        )

        if message is None:
            print(
                "Message not found."
            )
            return 1

        subject = message.headers.fields.get(
            "Subject",
            "(no subject)",
        )

        print(f"Message ID: {message_id}")
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
    message_ids = store.list_messages(
        mailbox
    )

    try:
        position = int(reference)
    except ValueError:
        return (
            reference
            if reference in message_ids
            else None
        )

    if position < 1:
        return None

    index = position - 1

    if index >= len(message_ids):
        return None

    return message_ids[index]