# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.storage.memory.backend import (
    MemoryMessageStoreBackend,
)
from garlicsmtp.storage.store import (
    MessageStore,
)
from garlicsmtp.storage.entry import (
    VerificationStatus,
)
from datetime import UTC, datetime


def test_memory_message_store_saves_message(
    message,
):

    store = MemoryMessageStoreBackend()

    message_id = store.save(
        "bob",
        message,
    )

    assert message_id in store.list_messages(
        "bob"
    )

    assert store.get(
        "bob",
        message_id,
    ) is message


def test_memory_message_store_separates_mailboxes(
    message,
):

    store = MemoryMessageStoreBackend()

    message_id = store.save(
        "bob",
        message,
    )

    assert message_id in store.list_messages(
        "bob"
    )

    assert store.list_messages(
        "alice"
    ) == []


def test_memory_message_store_lists_mailboxes(
    message,
):

    store = MemoryMessageStoreBackend()

    store.save(
        "bob@test.onion",
        message,
    )

    store.save(
        "alice@test.onion",
        message,
    )

    assert set(
        store.list_mailboxes()
    ) == {
        "alice@test.onion",
        "bob@test.onion",
    }


def test_memory_message_store_counts_messages(
    message,
):

    store = MemoryMessageStoreBackend()

    store.save(
        "bob@test.onion",
        message,
    )

    store.save(
        "bob@test.onion",
        message,
    )

    assert store.count(
        "bob@test.onion"
    ) == 2

    assert store.count(
        "alice@test.onion"
    ) == 0


def test_memory_message_store_entry_api(
    message,
):
    backend = MemoryMessageStoreBackend()

    first = backend.save_entry(
        "bob@test.onion",
        message,
    )

    second = backend.save_entry(
        "bob@test.onion",
        message,
    )

    other = backend.save_entry(
        "alice@test.onion",
        message,
    )

    assert first.uid == 1
    assert second.uid == 2
    assert other.uid == 1

    assert backend.get_entry(
        "bob@test.onion",
        first.id,
    ) is first

    assert [
        entry.uid
        for entry in backend.list_entries(
            "bob@test.onion"
        )
    ] == [1, 2]


def test_memory_message_store_updates_flags(
    message,
):
    backend = MemoryMessageStoreBackend()

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


def test_memory_message_store_returns_false_for_missing_flags_update():

    backend = MemoryMessageStoreBackend()

    assert backend.set_flags(
        "bob@test.onion",
        "missing",
        {
            "\\Seen",
        },
    ) is False


def test_memory_message_store_adds_and_removes_flags(
    message,
):
    backend = MemoryMessageStoreBackend()

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


def test_memory_store_copies_entry(
    message,
):
    store = MessageStore()

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

    assert copied.message == source.message
    assert copied.flags == {
        "\\Seen",
        "\\Flagged",
    }

    assert (
        copied.internal_date
        == source.internal_date
    )

    restored_source = store.get_entry(
        "source@test.onion",
        source.id,
    )

    assert restored_source is not None


def test_memory_store_copy_returns_none_for_missing_entry(
    message,
):
    store = MessageStore()

    store.save_entry(
        "destination@test.onion",
        message,
    )

    assert store.copy_entry(
        "source@test.onion",
        "missing",
        "destination@test.onion",
    ) is None


def test_memory_store_appends_entry_with_metadata(
    message,
):
    store = MessageStore()

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

    assert entry.mailbox == (
        "archive@test.onion"
    )

    assert entry.uid == 1
    assert entry.message == message

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
    assert restored.uid == 1

    assert restored.flags == {
        "\\Seen",
        "\\Flagged",
    }

    assert (
        restored.internal_date
        == internal_date
    )


def test_memory_store_append_assigns_next_uid(
    message,
):
    store = MessageStore()

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


def test_memory_store_append_copies_flags(
    message,
):
    store = MessageStore()

    flags = {
        "\\Seen",
    }

    entry = store.append_entry(
        "archive@test.onion",
        message,
        flags,
        datetime(
            2026,
            7,
            15,
            tzinfo=UTC,
        ),
    )

    flags.add(
        "\\Deleted"
    )

    assert entry.flags == {
        "\\Seen",
    }


def test_memory_store_creates_empty_mailbox():
    backend = MemoryMessageStoreBackend()

    assert backend.create_mailbox(
        "archive@test.onion"
    ) is True

    assert backend.list_mailboxes() == [
        "archive@test.onion",
    ]

    assert backend.count(
        "archive@test.onion"
    ) == 0


def test_memory_store_preserves_created_mailbox_after_reads():
    backend = MemoryMessageStoreBackend()

    backend.create_mailbox(
        "archive@test.onion"
    )

    assert backend.list_messages(
        "missing@test.onion"
    ) == []

    assert backend.list_mailboxes() == [
        "archive@test.onion",
    ]


def test_memory_store_deletes_mailbox_and_messages(
    message,
):
    backend = MemoryMessageStoreBackend()

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


def test_memory_store_recreated_mailbox_restarts_uid(
    message,
):
    backend = MemoryMessageStoreBackend()

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


def test_memory_store_renames_mailbox_and_preserves_uid(
    message,
):
    backend = MemoryMessageStoreBackend()

    entry = backend.save_entry(
        "Archive",
        message,
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
    assert renamed_entries[0].uid == entry.uid

    next_entry = backend.save_entry(
        "Old",
        message,
    )

    assert next_entry.uid == entry.uid + 1


def test_memory_store_rename_rejects_existing_destination():
    backend = MemoryMessageStoreBackend()

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


def test_memory_store_manages_subscriptions():
    backend = MemoryMessageStoreBackend()

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


def test_memory_store_delete_removes_subscription():
    backend = MemoryMessageStoreBackend()

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


def test_memory_store_rename_moves_subscription():
    backend = MemoryMessageStoreBackend()

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


def test_memory_save_entry_preserves_verification_status(
    message,
):
    backend = MemoryMessageStoreBackend()

    entry = backend.save_entry(
        "bob@test.onion",
        message,
        verification_status=(
            VerificationStatus.VERIFIED
        ),
    )

    restored = backend.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert restored is not None
    assert restored.verification_status == (
        VerificationStatus.VERIFIED
    )