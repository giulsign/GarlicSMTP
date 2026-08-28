# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.storage.sqlite import (
    SQLiteMessageStoreBackend,
)
import json
import sqlite3
from garlicsmtp.storage.serializer import (
    MessageSerializer,
)
from garlicsmtp.storage.store import MessageStore
from datetime import UTC, datetime


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

    def test_sqlite_message_store_assigns_mailbox_uids(
        tmp_path,
        message,
    ):
        database = tmp_path / "mailboxes.db"

        backend = SQLiteMessageStoreBackend(
            database
        )

        try:
            first_id = backend.save(
                "bob@test.onion",
                message,
            )

            second_id = backend.save(
                "bob@test.onion",
                message,
            )

            other_id = backend.save(
                "alice@test.onion",
                message,
            )

            rows = backend.connection.execute(
                """
                SELECT id, mailbox, uid
                FROM messages
                ORDER BY rowid ASC
                """
            ).fetchall()

            assert rows == [
                (
                    first_id,
                    "bob@test.onion",
                    1,
                ),
                (
                    second_id,
                    "bob@test.onion",
                    2,
                ),
                (
                    other_id,
                    "alice@test.onion",
                    1,
                ),
            ]

        finally:
            backend.close()


def test_sqlite_message_store_assigns_mailbox_uids(
    tmp_path,
    message,
):
    database = tmp_path / "mailboxes.db"

    backend = SQLiteMessageStoreBackend(
        database
    )

    try:
        first_id = backend.save(
            "bob@test.onion",
            message,
        )

        second_id = backend.save(
            "bob@test.onion",
            message,
        )

        other_id = backend.save(
            "alice@test.onion",
            message,
        )

        rows = backend.connection.execute(
            """
            SELECT id, mailbox, uid
            FROM messages
            ORDER BY rowid ASC
            """
        ).fetchall()

        assert rows == [
            (
                first_id,
                "bob@test.onion",
                1,
            ),
            (
                second_id,
                "bob@test.onion",
                2,
            ),
            (
                other_id,
                "alice@test.onion",
                1,
            ),
        ]

    finally:
        backend.close()


def test_sqlite_message_store_saves_entry_metadata(
    tmp_path,
    message,
):
    database = tmp_path / "mailboxes.db"

    backend = SQLiteMessageStoreBackend(
        database
    )

    try:
        message_id = backend.save(
            "bob@test.onion",
            message,
        )

        row = backend.connection.execute(
            """
            SELECT uid, internal_date, flags
            FROM messages
            WHERE id = ?
            """,
            (message_id,),
        ).fetchone()

        assert row is not None

        uid, internal_date, flags = row

        assert uid == 1
        assert internal_date is not None
        assert json.loads(flags) == []

    finally:
        backend.close()


def test_sqlite_message_store_migrates_old_schema(
    tmp_path,
    message,
):
    database = tmp_path / "old-mailboxes.db"

    connection = sqlite3.connect(
        database
    )

    connection.execute(
        """
        CREATE TABLE messages (
            id TEXT PRIMARY KEY,
            mailbox TEXT NOT NULL,
            payload TEXT NOT NULL,
            created TEXT NOT NULL
        )
        """
    )

    connection.execute(
        """
        INSERT INTO messages (
            id,
            mailbox,
            payload,
            created
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            "old-message",
            "bob@test.onion",
            MessageSerializer.to_json(
                message
            ),
            "2030-01-01T12:00:00+00:00",
        ),
    )

    connection.commit()
    connection.close()

    backend = SQLiteMessageStoreBackend(
        database
    )

    try:
        row = backend.connection.execute(
            """
            SELECT uid, internal_date, flags
            FROM messages
            WHERE id = ?
            """,
            ("old-message",),
        ).fetchone()

        assert row == (
            1,
            "2030-01-01T12:00:00+00:00",
            "[]",
        )

        restored = backend.get(
            "bob@test.onion",
            "old-message",
        )

        assert restored is not None
        assert (
            restored.envelope.sender
            == message.envelope.sender
        )

    finally:
        backend.close()


def test_sqlite_message_store_entry_api(
    tmp_path,
    message,
):
    backend = SQLiteMessageStoreBackend(
        tmp_path / "mailboxes.db"
    )

    try:
        first = backend.save_entry(
            "bob@test.onion",
            message,
        )

        second = backend.save_entry(
            "bob@test.onion",
            message,
        )

        assert first.uid == 1
        assert second.uid == 2
        assert first.flags == set()

        restored = backend.get_entry(
            "bob@test.onion",
            first.id,
        )

        assert restored is not None
        assert restored.uid == 1
        assert restored.message.body == (
            message.body
        )

        entries = backend.list_entries(
            "bob@test.onion"
        )

        assert [
            entry.uid
            for entry in entries
        ] == [1, 2]

    finally:
        backend.close()


def test_sqlite_message_store_updates_flags(
    tmp_path,
    message,
):
    backend = SQLiteMessageStoreBackend(
        tmp_path / "mailboxes.db"
    )

    try:
        entry = backend.save_entry(
            "bob@test.onion",
            message,
        )

        result = backend.set_flags(
            "bob@test.onion",
            entry.id,
            {
                "\\Seen",
                "\\Flagged",
            },
        )

        assert result is True

        restored = backend.get_entry(
            "bob@test.onion",
            entry.id,
        )

        assert restored is not None
        assert restored.flags == {
            "\\Seen",
            "\\Flagged",
        }

    finally:
        backend.close()


def test_sqlite_message_store_returns_false_for_missing_flags_update(
    tmp_path,
):
    backend = SQLiteMessageStoreBackend(
        tmp_path / "mailboxes.db"
    )

    try:
        assert backend.set_flags(
            "bob@test.onion",
            "missing",
            {
                "\\Seen",
            },
        ) is False

    finally:
        backend.close()


def test_sqlite_message_store_adds_and_removes_flags(
    tmp_path,
    message,
):
    backend = SQLiteMessageStoreBackend(
        tmp_path / "mailboxes.db"
    )

    try:
        entry = backend.save_entry(
            "bob@test.onion",
            message,
        )

        assert backend.add_flags(
            "bob@test.onion",
            entry.id,
            {
                "\\Seen",
                "\\Flagged",
            },
        ) is True

        assert backend.remove_flags(
            "bob@test.onion",
            entry.id,
            {
                "\\Flagged",
            },
        ) is True

        restored = backend.get_entry(
            "bob@test.onion",
            entry.id,
        )

        assert restored is not None
        assert restored.flags == {
            "\\Seen",
        }

    finally:
        backend.close()


def test_sqlite_store_deletes_entry(
    tmp_path,
    message,
):
    backend = SQLiteMessageStoreBackend(
        tmp_path / "mailboxes.db"
    )

    store = MessageStore(
        backend=backend,
    )

    try:
        entry = store.save_entry(
            "bob@test.onion",
            message,
        )

        assert store.delete_entry(
            "bob@test.onion",
            entry.id,
        ) is True

        assert store.get_entry(
            "bob@test.onion",
            entry.id,
        ) is None

        assert store.delete_entry(
            "bob@test.onion",
            entry.id,
        ) is False

    finally:
        backend.close()


def test_sqlite_store_copies_entry(
    tmp_path,
    message,
):
    database = tmp_path / "mailboxes.db"

    store = MessageStore(
        SQLiteMessageStoreBackend(
            database
        )
    )

    source = store.save_entry(
        "source@test.onion",
        message,
    )

    store.set_flags(
        "source@test.onion",
        source.id,
        {
            "\\Seen",
            "\\Flagged",
        },
    )

    destination_seed = store.save_entry(
        "destination@test.onion",
        message,
    )

    copied = store.copy_entry(
        "source@test.onion",
        source.id,
        "destination@test.onion",
    )

    assert copied is not None

    assert copied.id != source.id
    assert copied.uid == (
        destination_seed.uid + 1
    )

    assert copied.mailbox == (
        "destination@test.onion"
    )

    assert copied.flags == {
        "\\Seen",
        "\\Flagged",
    }

    assert (
        copied.internal_date
        == source.internal_date
    )

    restored = store.get_entry(
        "destination@test.onion",
        copied.id,
    )

    assert restored is not None
    assert restored.uid == copied.uid
    assert restored.flags == copied.flags

    assert (
        restored.internal_date
        == source.internal_date
    )


def test_sqlite_store_copy_returns_none_for_missing_entry(
    tmp_path,
    message,
):
    database = tmp_path / "mailboxes.db"

    store = MessageStore(
        SQLiteMessageStoreBackend(
            database
        )
    )

    store.save_entry(
        "destination@test.onion",
        message,
    )

    assert store.copy_entry(
        "source@test.onion",
        "missing",
        "destination@test.onion",
    ) is None



def test_sqlite_store_appends_entry_with_metadata(
    tmp_path,
    message,
):
    database = tmp_path / "mailboxes.db"

    store = MessageStore(
        SQLiteMessageStoreBackend(
            database
        )
    )

    internal_date = datetime(
        2026,
        7,
        15,
        18,
        30,
        45,
        tzinfo=UTC,
    )

    entry = store.append_entry(
        "archive@test.onion",
        message,
        {
            "\\Seen",
            "\\Flagged",
        },
        internal_date,
    )

    assert entry.uid == 1

    assert entry.flags == {
        "\\Seen",
        "\\Flagged",
    }

    assert (
        entry.internal_date
        == internal_date
    )

    restored = store.get_entry(
        "archive@test.onion",
        entry.id,
    )

    assert restored is not None
    assert restored.uid == entry.uid
    assert restored.message == message

    assert restored.flags == {
        "\\Seen",
        "\\Flagged",
    }

    assert (
        restored.internal_date
        == internal_date
    )


def test_sqlite_store_append_assigns_next_uid(
    tmp_path,
    message,
):
    database = tmp_path / "mailboxes.db"

    store = MessageStore(
        SQLiteMessageStoreBackend(
            database
        )
    )

    first = store.save_entry(
        "archive@test.onion",
        message,
    )

    second = store.append_entry(
        "archive@test.onion",
        message,
        set(),
        datetime(
            2026,
            7,
            15,
            tzinfo=UTC,
        ),
    )

    assert second.uid == first.uid + 1


def test_sqlite_store_append_persists_after_reopen(
    tmp_path,
    message,
):
    database = tmp_path / "mailboxes.db"

    internal_date = datetime(
        2026,
        7,
        15,
        18,
        30,
        45,
        tzinfo=UTC,
    )

    first_store = MessageStore(
        SQLiteMessageStoreBackend(
            database
        )
    )

    created = first_store.append_entry(
        "archive@test.onion",
        message,
        {
            "\\Draft",
        },
        internal_date,
    )

    first_store.backend.connection.close()

    second_store = MessageStore(
        SQLiteMessageStoreBackend(
            database
        )
    )

    restored = second_store.get_entry(
        "archive@test.onion",
        created.id,
    )

    assert restored is not None
    assert restored.uid == created.uid

    assert restored.flags == {
        "\\Draft",
    }

    assert (
        restored.internal_date
        == internal_date
    )


def test_sqlite_store_creates_empty_mailbox(
    tmp_path,
):
    backend = SQLiteMessageStoreBackend(
        tmp_path / "mailboxes.db"
    )

    try:
        assert backend.create_mailbox(
            "archive@test.onion"
        ) is True

        assert backend.create_mailbox(
            "archive@test.onion"
        ) is False

        assert backend.list_mailboxes() == [
            "archive@test.onion",
        ]

        assert backend.count(
            "archive@test.onion"
        ) == 0

    finally:
        backend.close()


def test_sqlite_store_persists_empty_mailbox(
    tmp_path,
):
    database = tmp_path / "mailboxes.db"

    first_backend = SQLiteMessageStoreBackend(
        database
    )

    assert first_backend.create_mailbox(
        "archive@test.onion"
    ) is True

    first_backend.close()

    second_backend = SQLiteMessageStoreBackend(
        database
    )

    try:
        assert second_backend.list_mailboxes() == [
            "archive@test.onion",
        ]

    finally:
        second_backend.close()


def test_sqlite_store_migrates_existing_mailboxes(
    tmp_path,
    message,
):
    database = tmp_path / "mailboxes.db"

    connection = sqlite3.connect(
        database
    )

    connection.execute(
        """
        CREATE TABLE messages (
            id TEXT PRIMARY KEY,
            mailbox TEXT NOT NULL,
            uid INTEGER,
            payload TEXT NOT NULL,
            internal_date TEXT,
            flags TEXT,
            created TEXT NOT NULL
        )
        """
    )

    created = datetime.now(UTC).isoformat()

    connection.execute(
        """
        INSERT INTO messages (
            id,
            mailbox,
            uid,
            payload,
            internal_date,
            flags,
            created
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "existing-message",
            "archive@test.onion",
            1,
            MessageSerializer.to_json(
                message
            ),
            created,
            "[]",
            created,
        ),
    )

    connection.commit()
    connection.close()

    backend = SQLiteMessageStoreBackend(
        database
    )

    try:
        assert backend.list_mailboxes() == [
            "archive@test.onion",
        ]

    finally:
        backend.close()


def test_sqlite_store_deletes_mailbox_and_messages(
    tmp_path,
    message,
):
    backend = SQLiteMessageStoreBackend(
        tmp_path / "mailboxes.db"
    )

    try:
        backend.save_entry(
            "archive@test.onion",
            message,
        )

        assert backend.delete_mailbox(
            "archive@test.onion"
        ) is True

        assert backend.list_mailboxes() == []

        assert backend.list_entries(
            "archive@test.onion"
        ) == []

    finally:
        backend.close()


def test_sqlite_store_delete_returns_false_for_missing_mailbox(
    tmp_path,
):
    backend = SQLiteMessageStoreBackend(
        tmp_path / "mailboxes.db"
    )

    try:
        assert backend.delete_mailbox(
            "missing@test.onion"
        ) is False

    finally:
        backend.close()


def test_sqlite_store_persists_mailbox_deletion(
    tmp_path,
    message,
):
    database = tmp_path / "mailboxes.db"

    first_backend = SQLiteMessageStoreBackend(
        database
    )

    first_backend.save_entry(
        "archive@test.onion",
        message,
    )

    assert first_backend.delete_mailbox(
        "archive@test.onion"
    ) is True

    first_backend.close()

    second_backend = SQLiteMessageStoreBackend(
        database
    )

    try:
        assert second_backend.list_mailboxes() == []

        assert second_backend.list_entries(
            "archive@test.onion"
        ) == []

    finally:
        second_backend.close()


def test_sqlite_store_recreated_mailbox_restarts_uid(
    tmp_path,
    message,
):
    backend = SQLiteMessageStoreBackend(
        tmp_path / "mailboxes.db"
    )

    try:
        first = backend.save_entry(
            "archive@test.onion",
            message,
        )

        assert first.uid == 1

        backend.delete_mailbox(
            "archive@test.onion"
        )

        backend.create_mailbox(
            "archive@test.onion"
        )

        recreated = backend.save_entry(
            "archive@test.onion",
            message,
        )

        assert recreated.uid == 1

    finally:
        backend.close()


def test_sqlite_store_renames_mailbox_and_preserves_messages(
    tmp_path,
    message,
):
    backend = SQLiteMessageStoreBackend(
        tmp_path / "mailboxes.db"
    )

    try:
        entry = backend.save_entry(
            "Archive",
            message,
        )

        backend.add_flags(
            "Archive",
            entry.id,
            {
                "\\Seen",
            },
        )

        assert backend.rename_mailbox(
            "Archive",
            "Old",
        ) is True

        assert backend.list_mailboxes() == [
            "Old",
        ]

        renamed_entries = backend.list_entries(
            "Old"
        )

        assert len(renamed_entries) == 1
        assert renamed_entries[0].id == entry.id
        assert renamed_entries[0].uid == entry.uid
        assert renamed_entries[0].flags == {
            "\\Seen",
        }

    finally:
        backend.close()


def test_sqlite_store_rename_rejects_existing_destination(
    tmp_path,
):
    backend = SQLiteMessageStoreBackend(
        tmp_path / "mailboxes.db"
    )

    try:
        backend.create_mailbox(
            "Archive"
        )

        backend.create_mailbox(
            "Old"
        )

        assert backend.rename_mailbox(
            "Archive",
            "Old",
        ) is False

        assert backend.list_mailboxes() == [
            "Archive",
            "Old",
        ]

    finally:
        backend.close()


def test_sqlite_store_persists_mailbox_rename(
    tmp_path,
    message,
):
    database = tmp_path / "mailboxes.db"

    first_backend = SQLiteMessageStoreBackend(
        database
    )

    entry = first_backend.save_entry(
        "Archive",
        message,
    )

    assert first_backend.rename_mailbox(
        "Archive",
        "Old",
    ) is True

    first_backend.close()

    second_backend = SQLiteMessageStoreBackend(
        database
    )

    try:
        assert second_backend.list_mailboxes() == [
            "Old",
        ]

        renamed_entries = second_backend.list_entries(
            "Old"
        )

        assert len(renamed_entries) == 1
        assert renamed_entries[0].id == entry.id
        assert renamed_entries[0].uid == entry.uid

    finally:
        second_backend.close()


def test_sqlite_store_manages_subscriptions(
    tmp_path,
):
    backend = SQLiteMessageStoreBackend(
        tmp_path / "mailboxes.db"
    )

    try:
        backend.create_mailbox(
            "Archive"
        )

        assert backend.subscribe_mailbox(
            "Archive"
        ) is True

        assert backend.subscribe_mailbox(
            "Archive"
        ) is True

        assert backend.list_subscribed_mailboxes() == [
            "Archive",
        ]

        assert backend.unsubscribe_mailbox(
            "Archive"
        ) is True

        assert backend.unsubscribe_mailbox(
            "Archive"
        ) is False

    finally:
        backend.close()


def test_sqlite_store_persists_subscriptions(
    tmp_path,
):
    database = tmp_path / "mailboxes.db"

    first_backend = SQLiteMessageStoreBackend(
        database
    )

    first_backend.create_mailbox(
        "Archive"
    )

    first_backend.subscribe_mailbox(
        "Archive"
    )

    first_backend.close()

    second_backend = SQLiteMessageStoreBackend(
        database
    )

    try:
        assert second_backend.list_subscribed_mailboxes() == [
            "Archive",
        ]

    finally:
        second_backend.close()


def test_sqlite_store_delete_removes_subscription(
    tmp_path,
):
    backend = SQLiteMessageStoreBackend(
        tmp_path / "mailboxes.db"
    )

    try:
        backend.create_mailbox(
            "Archive"
        )

        backend.subscribe_mailbox(
            "Archive"
        )

        backend.delete_mailbox(
            "Archive"
        )

        assert backend.list_subscribed_mailboxes() == []

    finally:
        backend.close()


def test_sqlite_store_rename_moves_subscription(
    tmp_path,
):
    backend = SQLiteMessageStoreBackend(
        tmp_path / "mailboxes.db"
    )

    try:
        backend.create_mailbox(
            "Archive"
        )

        backend.subscribe_mailbox(
            "Archive"
        )

        backend.rename_mailbox(
            "Archive",
            "Old",
        )

        assert backend.list_subscribed_mailboxes() == [
            "Old",
        ]

    finally:
        backend.close()


def test_sqlite_uid_validity_persists_after_reopen(
    tmp_path,
):
    path = tmp_path / "mailboxes.db"

    backend = SQLiteMessageStoreBackend(
        path
    )

    store = MessageStore(
        backend=backend
    )

    store.create_mailbox(
        "test"
    )

    before = (
        store.open_mailbox(
            "test"
        ).uid_validity()
    )

    backend.close()

    reopened_backend = (
        SQLiteMessageStoreBackend(
            path
        )
    )

    reopened_store = MessageStore(
        backend=reopened_backend
    )

    after = (
        reopened_store.open_mailbox(
            "test"
        ).uid_validity()
    )

    assert after == before

    reopened_backend.close()


def test_sqlite_uid_validity_survives_rename(
    tmp_path,
):
    backend = SQLiteMessageStoreBackend(
        tmp_path / "mailboxes.db"
    )

    store = MessageStore(
        backend=backend
    )

    store.create_mailbox(
        "source"
    )

    before = (
        store.open_mailbox(
            "source"
        ).uid_validity()
    )

    store.rename_mailbox(
        "source",
        "destination",
    )

    after = (
        store.open_mailbox(
            "destination"
        ).uid_validity()
    )

    assert after == before

    backend.close()


def test_sqlite_recreated_mailbox_gets_new_uid_validity(
    tmp_path,
):
    backend = SQLiteMessageStoreBackend(
        tmp_path / "mailboxes.db"
    )

    store = MessageStore(
        backend=backend
    )

    store.create_mailbox(
        "test"
    )

    before = (
        store.open_mailbox(
            "test"
        ).uid_validity()
    )

    store.delete_mailbox(
        "test"
    )

    store.create_mailbox(
        "test"
    )

    after = (
        store.open_mailbox(
            "test"
        ).uid_validity()
    )

    assert after != before

    backend.close()