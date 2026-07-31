from garlicsmtp.storage.store import MessageStore

from garlicsmtp.storage.sqlite import (
    SQLiteMessageStoreBackend,
)
from garlicsmtp.storage.mailbox import (
    StoreOperation,
)
from datetime import UTC, datetime


def test_mailbox_view_lists_entries(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    mailbox = store.open_mailbox(
        "bob@test.onion"
    )

    assert [
        entry.id
        for entry in mailbox.list_entries()
    ] == [
        first.id,
        second.id,
    ]

    assert mailbox.count() == 2


def test_mailbox_view_gets_entry_by_uid(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    mailbox = store.open_mailbox(
        "bob@test.onion"
    )

    assert mailbox.get_by_uid(
        1
    ) is first

    assert mailbox.get_by_uid(
        2
    ) is second

    assert mailbox.get_by_uid(
        99
    ) is None


def test_mailbox_view_gets_sequence_number(
    message,
):
    store = MessageStore()

    store.save_entry(
        "bob@test.onion",
        message,
    )

    store.save_entry(
        "bob@test.onion",
        message,
    )

    mailbox = store.open_mailbox(
        "bob@test.onion"
    )

    assert mailbox.get_sequence_number(
        1
    ) == 1

    assert mailbox.get_sequence_number(
        2
    ) == 2

    assert mailbox.get_sequence_number(
        99
    ) is None


def test_mailbox_view_reports_next_uid(
    message,
):
    store = MessageStore()

    mailbox = store.open_mailbox(
        "bob@test.onion"
    )

    assert mailbox.next_uid() == 1

    store.save_entry(
        "bob@test.onion",
        message,
    )

    store.save_entry(
        "bob@test.onion",
        message,
    )

    assert mailbox.next_uid() == 3


def test_mailbox_view_reports_first_unseen_uid(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    store.add_flags(
        "bob@test.onion",
        first.id,
        {
            "\\Seen",
        },
    )

    mailbox = store.open_mailbox(
        "bob@test.onion"
    )

    assert mailbox.first_unseen_uid() == (
        second.uid
    )


def test_mailbox_view_updates_flags(
    message,
):
    store = MessageStore()

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    mailbox = store.open_mailbox(
        "bob@test.onion"
    )

    assert mailbox.add_flags(
        entry.id,
        {
            "\\Seen",
            "\\Flagged",
        },
    ) is True

    restored = mailbox.get_by_uid(
        entry.uid
    )

    assert restored is not None
    assert restored.flags == {
        "\\Seen",
        "\\Flagged",
    }

    assert mailbox.remove_flags(
        entry.id,
        {
            "\\Flagged",
        },
    ) is True

    restored = mailbox.get_by_uid(
        entry.uid
    )

    assert restored is not None
    assert restored.flags == {
        "\\Seen",
    }


def test_mailbox_view_works_with_sqlite(
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
        first = store.save_entry(
            "bob@test.onion",
            message,
        )

        second = store.save_entry(
            "bob@test.onion",
            message,
        )

        mailbox = store.open_mailbox(
            "bob@test.onion"
        )

        assert mailbox.count() == 2
        assert mailbox.next_uid() == 3

        restored = mailbox.get_by_uid(
            second.uid
        )

        assert restored is not None
        assert restored.id == second.id

        assert mailbox.get_sequence_number(
            first.uid
        ) == 1

    finally:
        backend.close()

def test_mailbox_view_gets_entry_and_sequence_by_uid(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    mailbox = store.open_mailbox(
        "bob@test.onion"
    )

    result = mailbox.get_by_uid_with_sequence(
        second.uid
    )

    assert result is not None

    sequence_number, restored = result

    assert sequence_number == 2
    assert restored.id == second.id

    assert mailbox.get_by_uid_with_sequence(
        99
    ) is None


def test_mailbox_view_deletes_entry(
    message,
):
    store = MessageStore()

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    mailbox = store.open_mailbox(
        "bob@test.onion"
    )

    assert mailbox.delete(
        entry.id
    ) is True

    assert mailbox.get_by_id(
        entry.id
    ) is None

    assert mailbox.count() == 0


def test_mailbox_view_expunges_deleted_entries(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    third = store.save_entry(
        "bob@test.onion",
        message,
    )

    mailbox = store.open_mailbox(
        "bob@test.onion"
    )

    assert mailbox.add_flags(
        second.id,
        {"\\Deleted"},
    ) is True

    assert mailbox.add_flags(
        third.id,
        {"\\Deleted"},
    ) is True

    assert mailbox.expunge_deleted() == [
        2,
        2,
    ]

    remaining = mailbox.list_entries()

    assert [
        entry.id
        for entry in remaining
    ] == [
        first.id,
    ]


def test_mailbox_view_expunge_does_nothing_without_deleted_entries(
    message,
):
    store = MessageStore()

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    mailbox = store.open_mailbox(
        "bob@test.onion"
    )

    assert mailbox.expunge_deleted() == []

    remaining = mailbox.list_entries()

    assert len(remaining) == 1
    assert remaining[0].id == entry.id


def test_mailbox_view_expunge_recalculates_sequence_numbers(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    third = store.save_entry(
        "bob@test.onion",
        message,
    )

    fourth = store.save_entry(
        "bob@test.onion",
        message,
    )

    mailbox = store.open_mailbox(
        "bob@test.onion"
    )

    mailbox.add_flags(
        first.id,
        {"\\Deleted"},
    )

    mailbox.add_flags(
        third.id,
        {"\\Deleted"},
    )

    assert mailbox.expunge_deleted() == [
        1,
        2,
    ]

    assert [
        entry.id
        for entry in mailbox.list_entries()
    ] == [
        second.id,
        fourth.id,
    ]


def test_mailbox_view_fetches_entry_by_uid(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    mailbox = store.open_mailbox(
        "bob@test.onion"
    )

    result = mailbox.fetch_by_uid(
        second.uid
    )

    assert result is not None

    sequence_number, entry = result

    assert sequence_number == 2
    assert entry.id == second.id
    assert entry.id != first.id


def test_mailbox_view_fetch_by_uid_returns_none(
    message,
):
    store = MessageStore()

    store.save_entry(
        "bob@test.onion",
        message,
    )

    mailbox = store.open_mailbox(
        "bob@test.onion"
    )

    assert mailbox.fetch_by_uid(
        999
    ) is None


def test_mailbox_view_sets_flags_by_uid(
    message,
):
    store = MessageStore()

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    mailbox = store.open_mailbox(
        "bob@test.onion"
    )

    result = mailbox.store_flags(
        uid=entry.uid,
        operation=StoreOperation.SET,
        flags={
            "\\Seen",
            "\\Flagged",
        },
    )

    assert result is not None

    sequence_number, refreshed = result

    assert sequence_number == 1
    assert refreshed.flags == {
        "\\Seen",
        "\\Flagged",
    }


def test_mailbox_view_adds_flags_by_uid(
    message,
):
    store = MessageStore()

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    mailbox = store.open_mailbox(
        "bob@test.onion"
    )

    mailbox.add_flags(
        entry.id,
        {
            "\\Seen",
        },
    )

    result = mailbox.store_flags(
        uid=entry.uid,
        operation=StoreOperation.ADD,
        flags={
            "\\Flagged",
        },
    )

    assert result is not None

    _, refreshed = result

    assert refreshed.flags == {
        "\\Seen",
        "\\Flagged",
    }


def test_mailbox_view_removes_flags_by_uid(
    message,
):
    store = MessageStore()

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    mailbox = store.open_mailbox(
        "bob@test.onion"
    )

    mailbox.add_flags(
        entry.id,
        {
            "\\Seen",
            "\\Flagged",
        },
    )

    result = mailbox.store_flags(
        uid=entry.uid,
        operation=StoreOperation.REMOVE,
        flags={
            "\\Flagged",
        },
    )

    assert result is not None

    _, refreshed = result

    assert refreshed.flags == {
        "\\Seen",
    }


def test_mailbox_view_store_flags_returns_none_for_missing_uid(
    message,
):
    store = MessageStore()

    store.save_entry(
        "bob@test.onion",
        message,
    )

    mailbox = store.open_mailbox(
        "bob@test.onion"
    )

    assert mailbox.store_flags(
        uid=999,
        operation=StoreOperation.ADD,
        flags={
            "\\Seen",
        },
    ) is None


def test_mailbox_view_counts_unseen_messages(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    store.save_entry(
        "bob@test.onion",
        message,
    )

    store.save_entry(
        "bob@test.onion",
        message,
    )

    store.add_flags(
        "bob@test.onion",
        first.id,
        {
            "\\Seen",
        },
    )

    mailbox = store.open_mailbox(
        "bob@test.onion"
    )

    assert mailbox.unseen_count() == 2


def test_mailbox_view_unseen_count_is_zero_when_all_seen(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    store.add_flags(
        "bob@test.onion",
        first.id,
        {
            "\\Seen",
        },
    )

    store.add_flags(
        "bob@test.onion",
        second.id,
        {
            "\\Seen",
        },
    )

    mailbox = store.open_mailbox(
        "bob@test.onion"
    )

    assert mailbox.unseen_count() == 0


def test_mailbox_view_appends_message_with_metadata(
    message,
):
    store = MessageStore()

    store.save_entry(
        "archive@test.onion",
        message,
    )

    mailbox = store.open_mailbox(
        "archive@test.onion"
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

    appended = mailbox.append_message(
        message,
        flags={
            "\\Seen",
            "\\Draft",
        },
        internal_date=internal_date,
    )

    assert appended.uid == 2

    assert appended.flags == {
        "\\Seen",
        "\\Draft",
    }

    assert (
        appended.internal_date
        == internal_date
    )

    entries = mailbox.list_entries()

    assert [
        entry.uid
        for entry in entries
    ] == [
        1,
        2,
    ]


def test_mailbox_view_append_uses_defaults(
    message,
):
    store = MessageStore()

    store.save_entry(
        "archive@test.onion",
        message,
    )

    mailbox = store.open_mailbox(
        "archive@test.onion"
    )

    before = datetime.now(UTC)

    appended = mailbox.append_message(
        message
    )

    after = datetime.now(UTC)

    assert appended.flags == set()

    assert (
        before
        <= appended.internal_date
        <= after
    )


def test_mailbox_view_append_does_not_change_selection_state(
    message,
):
    store = MessageStore()

    store.save_entry(
        "archive@test.onion",
        message,
    )

    mailbox = store.open_mailbox(
        "archive@test.onion"
    )

    appended = mailbox.append_message(
        message
    )

    assert appended.mailbox == (
        "archive@test.onion"
    )

    assert mailbox.count() == 2



def test_mailbox_view_copies_message_by_uid(
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
        },
    )

    destination_seed = store.save_entry(
        "destination@test.onion",
        message,
    )

    mailbox = store.open_mailbox(
        "source@test.onion"
    )

    result = mailbox.copy_by_uid(
        source.uid,
        "destination@test.onion",
    )

    assert result == (
        source.uid,
        destination_seed.uid + 1,
    )

    destination_entries = (
        store.list_entries(
            "destination@test.onion"
        )
    )

    copied = destination_entries[-1]

    assert copied.flags == {
        "\\Seen",
    }

    assert (
        copied.internal_date
        == source.internal_date
    )


def test_mailbox_view_moves_message_by_uid(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "source@test.onion",
        message,
    )

    moved_source = store.save_entry(
        "source@test.onion",
        message,
    )

    third = store.save_entry(
        "source@test.onion",
        message,
    )

    store.set_flags(
        "source@test.onion",
        moved_source.id,
        {
            "\\Seen",
            "\\Flagged",
        },
    )

    destination_seed = store.save_entry(
        "destination@test.onion",
        message,
    )

    mailbox = store.open_mailbox(
        "source@test.onion"
    )

    result = mailbox.move_by_uid(
        moved_source.uid,
        "destination@test.onion",
    )

    assert result == (
        moved_source.uid,
        destination_seed.uid + 1,
        2,
    )

    source_entries = store.list_entries(
        "source@test.onion"
    )

    assert [
        entry.id
        for entry in source_entries
    ] == [
        first.id,
        third.id,
    ]

    destination_entries = (
        store.list_entries(
            "destination@test.onion"
        )
    )

    assert len(destination_entries) == 2

    copied = destination_entries[-1]

    assert copied.id != moved_source.id
    assert copied.uid == (
        destination_seed.uid + 1
    )

    assert copied.flags == {
        "\\Seen",
        "\\Flagged",
    }

    assert (
        copied.internal_date
        == moved_source.internal_date
    )


def test_mailbox_view_move_returns_none_for_missing_uid(
    message,
):
    store = MessageStore()

    store.save_entry(
        "source@test.onion",
        message,
    )

    store.save_entry(
        "destination@test.onion",
        message,
    )

    mailbox = store.open_mailbox(
        "source@test.onion"
    )

    assert mailbox.move_by_uid(
        999,
        "destination@test.onion",
    ) is None


def test_mailbox_view_copy_returns_none_for_missing_uid(
    message,
):
    store = MessageStore()

    store.save_entry(
        "source@test.onion",
        message,
    )

    store.save_entry(
        "destination@test.onion",
        message,
    )

    mailbox = store.open_mailbox(
        "source@test.onion"
    )

    assert mailbox.copy_by_uid(
        999,
        "destination@test.onion",
    ) is None


def test_mailbox_view_get_by_sequence_number(
    message,
):
    store = MessageStore()

    first = store.save_entry(
        "bob@test.onion",
        message,
    )

    second = store.save_entry(
        "bob@test.onion",
        message,
    )

    mailbox = store.open_mailbox(
        "bob@test.onion"
    )

    assert (
        mailbox.get_by_sequence_number(1)
        == first
    )

    assert (
        mailbox.get_by_sequence_number(2)
        == second
    )

    assert (
        mailbox.get_by_sequence_number(3)
        is None
    )

    assert (
        mailbox.get_by_sequence_number(0)
        is None
    )