from garlicsmtp.storage.sqlite import (
    SQLiteMessageStoreBackend,
)


def test_sqlite_message_store_persists_message(
    tmp_path,
    message,
):

    db_path = tmp_path / "mailboxes.db"

    backend = SQLiteMessageStoreBackend(
        db_path
    )

    message.headers.fields[
        "Subject"
    ] = "Persistent mailbox"

    message.body = "Stored permanently"

    message_id = backend.save(
        "bob@test.onion",
        message,
    )

    backend.close()

    restored_backend = (
        SQLiteMessageStoreBackend(
            db_path
        )
    )

    try:
        ids = restored_backend.list_messages(
            "bob@test.onion"
        )

        assert ids == [
            message_id
        ]

        restored = restored_backend.get(
            "bob@test.onion",
            message_id,
        )

        assert restored is not None

        assert (
            restored.envelope.sender
            == message.envelope.sender
        )

        assert (
            restored.envelope.recipients
            == message.envelope.recipients
        )

        assert (
            restored.headers.fields.get(
                "Subject"
            )
            == "Persistent mailbox"
        )

        assert (
            restored.body
            == "Stored permanently"
        )

    finally:
        restored_backend.close()


def test_sqlite_message_store_lists_mailboxes(
    tmp_path,
    message,
):

    backend = SQLiteMessageStoreBackend(
        tmp_path / "mailboxes.db"
    )

    try:
        backend.save(
            "bob@test.onion",
            message,
        )

        backend.save(
            "alice@test.onion",
            message,
        )

        assert backend.list_mailboxes() == [
            "alice@test.onion",
            "bob@test.onion",
        ]

    finally:
        backend.close()


def test_sqlite_message_store_counts_messages(
    tmp_path,
    message,
):

    backend = SQLiteMessageStoreBackend(
        tmp_path / "mailboxes.db"
    )

    try:
        backend.save(
            "bob@test.onion",
            message,
        )

        backend.save(
            "bob@test.onion",
            message,
        )

        assert backend.count(
            "bob@test.onion"
        ) == 2

        assert backend.count(
            "alice@test.onion"
        ) == 0

    finally:
        backend.close()