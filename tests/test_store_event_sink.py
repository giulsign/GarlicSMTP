from datetime import UTC, datetime

from garlicsmtp.storage.event_sink import (
    StoreEventSink,
)
from garlicsmtp.storage.null_event_sink import (
    NullStoreEventSink,
)
from garlicsmtp.storage.store import (
    MessageStore,
)
from garlicsmtp.storage.composite_event_sink import (
    CompositeStoreEventSink,
)


def test_null_store_event_sink_accepts_events():
    sink = NullStoreEventSink()

    sink.message_added(
        "bob@test.onion"
    )

    sink.message_removed(
        "bob@test.onion",
        1,
    )

    sink.flags_changed(
        "bob@test.onion"
    )


class RecordingStoreEventSink(
    StoreEventSink
):

    def __init__(self):
        self.added = []
        self.removed = []
        self.changed = []

    def message_added(
        self,
        mailbox: str,
    ) -> None:
        self.added.append(
            mailbox
        )

    def message_removed(
        self,
        mailbox: str,
        sequence_number: int,
    ) -> None:
        self.removed.append(
            (
                mailbox,
                sequence_number,
            )
        )

    def flags_changed(
        self,
        mailbox: str,
    ) -> None:
        self.changed.append(
            mailbox
        )


def test_message_store_emits_message_added(
    message,
):
    sink = RecordingStoreEventSink()

    store = MessageStore(
        event_sink=sink
    )

    store.save(
        "bob@test.onion",
        message,
    )

    assert sink.added == [
        "bob@test.onion",
    ]


def test_message_store_append_emits_message_added(
    message,
):
    sink = RecordingStoreEventSink()

    store = MessageStore(
        event_sink=sink
    )

    store.append_entry(
        "bob@test.onion",
        message,
        set(),
        datetime.now(UTC),
    )

    assert sink.added == [
        "bob@test.onion",
    ]


def test_message_store_copy_emits_message_added(
    message,
):
    sink = RecordingStoreEventSink()

    store = MessageStore(
        event_sink=sink
    )

    source = store.save_entry(
        "source@test.onion",
        message,
    )

    sink.added.clear()

    store.create_mailbox(
        "destination@test.onion"
    )

    copied = store.copy_entry(
        "source@test.onion",
        source.id,
        "destination@test.onion",
    )

    assert copied is not None

    assert sink.added == [
        "destination@test.onion",
    ]


def test_message_store_failed_copy_emits_no_event(
    message,
):
    sink = RecordingStoreEventSink()

    store = MessageStore(
        event_sink=sink
    )

    store.create_mailbox(
        "source@test.onion"
    )

    store.create_mailbox(
        "destination@test.onion"
    )

    copied = store.copy_entry(
        "source@test.onion",
        "missing",
        "destination@test.onion",
    )

    assert copied is None
    assert sink.added == []


def test_message_store_set_flags_emits_flags_changed(
    message,
):
    sink = RecordingStoreEventSink()

    store = MessageStore(
        event_sink=sink
    )

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    sink.changed.clear()

    updated = store.set_flags(
        "bob@test.onion",
        entry.id,
        {
            "\\Seen",
        },
    )

    assert updated is True

    assert sink.changed == [
        "bob@test.onion",
    ]


def test_message_store_add_flags_emits_flags_changed(
    message,
):
    sink = RecordingStoreEventSink()

    store = MessageStore(
        event_sink=sink
    )

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    sink.changed.clear()

    updated = store.add_flags(
        "bob@test.onion",
        entry.id,
        {
            "\\Flagged",
        },
    )

    assert updated is True

    assert sink.changed == [
        "bob@test.onion",
    ]


def test_message_store_remove_flags_emits_flags_changed(
    message,
):
    sink = RecordingStoreEventSink()

    store = MessageStore(
        event_sink=sink
    )

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    store.add_flags(
        "bob@test.onion",
        entry.id,
        {
            "\\Seen",
        },
    )

    sink.changed.clear()

    updated = store.remove_flags(
        "bob@test.onion",
        entry.id,
        {
            "\\Seen",
        },
    )

    assert updated is True

    assert sink.changed == [
        "bob@test.onion",
    ]


def test_message_store_failed_flag_update_emits_no_event():
    sink = RecordingStoreEventSink()

    store = MessageStore(
        event_sink=sink
    )

    updated = store.add_flags(
        "bob@test.onion",
        "missing",
        {
            "\\Seen",
        },
    )

    assert updated is False
    assert sink.changed == []


def test_mailbox_expunge_emits_message_removed(
    message,
):
    sink = RecordingStoreEventSink()

    store = MessageStore(
        event_sink=sink
    )

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
            "\\Deleted",
        },
    )

    store.add_flags(
        "bob@test.onion",
        second.id,
        {
            "\\Deleted",
        },
    )

    sink.removed.clear()

    mailbox = store.open_mailbox(
        "bob@test.onion"
    )

    sequence_numbers = (
        mailbox.expunge_deleted()
    )

    assert sequence_numbers == [
        1,
        1,
    ]

    assert sink.removed == [
        (
            "bob@test.onion",
            1,
        ),
        (
            "bob@test.onion",
            1,
        ),
    ]


def test_mailbox_move_emits_added_and_removed_events(
    message,
):
    sink = RecordingStoreEventSink()

    store = MessageStore(
        event_sink=sink
    )

    source = store.save_entry(
        "source@test.onion",
        message,
    )

    store.create_mailbox(
        "destination@test.onion"
    )

    sink.added.clear()
    sink.removed.clear()

    mailbox = store.open_mailbox(
        "source@test.onion"
    )

    moved = mailbox.move_by_uid(
        source.uid,
        "destination@test.onion",
    )

    assert moved is not None

    assert sink.added == [
        "destination@test.onion",
    ]

    assert sink.removed == [
        (
            "source@test.onion",
            1,
        ),
    ]


def test_composite_store_event_sink_forwards_events():
    first = RecordingStoreEventSink()
    second = RecordingStoreEventSink()

    sink = CompositeStoreEventSink()

    sink.add(first)
    sink.add(second)

    sink.message_added(
        "bob@test.onion"
    )

    sink.message_removed(
        "bob@test.onion",
        2,
    )

    sink.flags_changed(
        "bob@test.onion"
    )

    assert first.added == [
        "bob@test.onion",
    ]

    assert second.added == [
        "bob@test.onion",
    ]

    assert first.removed == [
        (
            "bob@test.onion",
            2,
        ),
    ]

    assert second.removed == [
        (
            "bob@test.onion",
            2,
        ),
    ]

    assert first.changed == [
        "bob@test.onion",
    ]

    assert second.changed == [
        "bob@test.onion",
    ]


def test_composite_store_event_sink_removes_sink():
    first = RecordingStoreEventSink()
    second = RecordingStoreEventSink()

    sink = CompositeStoreEventSink()

    sink.add(first)
    sink.add(second)

    sink.remove(first)

    sink.message_added(
        "bob@test.onion"
    )

    assert first.added == []

    assert second.added == [
        "bob@test.onion",
    ]
