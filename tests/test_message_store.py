from garlicsmtp.storage.store import (
    MessageStore,
)


def test_message_store_delegates_to_backend(
    message,
):

    store = MessageStore()

    message_id = store.save(
        "bob",
        message,
    )

    assert message_id in store.list_messages(
        "bob"
    )

    assert (
        store.get(
            "bob",
            message_id,
        )
        is message
    )


def test_message_store_lists_and_counts(
    message,
):

    store = MessageStore()

    store.save(
        "bob@test.onion",
        message,
    )

    assert store.list_mailboxes() == [
        "bob@test.onion"
    ]

    assert store.count(
        "bob@test.onion"
    ) == 1


def test_message_store_updates_flags(
    message,
):
    store = MessageStore()

    entry = store.save_entry(
        "bob@test.onion",
        message,
    )

    assert store.set_flags(
        "bob@test.onion",
        entry.id,
        {
            "\\Seen",
        },
    ) is True

    restored = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert restored is not None
    assert restored.flags == {
        "\\Seen",
    }


def test_message_store_creates_empty_mailbox():
    store = MessageStore()

    assert store.create_mailbox(
        "archive@test.onion"
    ) is True

    assert store.list_mailboxes() == [
        "archive@test.onion",
    ]

    assert store.count(
        "archive@test.onion"
    ) == 0


def test_message_store_does_not_recreate_existing_mailbox():
    store = MessageStore()

    assert store.create_mailbox(
        "archive@test.onion"
    ) is True

    assert store.create_mailbox(
        "archive@test.onion"
    ) is False

    assert store.list_mailboxes() == [
        "archive@test.onion",
    ]


def test_message_store_deletes_mailbox(
    message,
):
    store = MessageStore()

    store.save_entry(
        "archive@test.onion",
        message,
    )

    assert store.delete_mailbox(
        "archive@test.onion"
    ) is True

    assert store.list_mailboxes() == []

    assert store.list_entries(
        "archive@test.onion"
    ) == []


def test_message_store_delete_returns_false_for_missing_mailbox():
    store = MessageStore()

    assert store.delete_mailbox(
        "missing@test.onion"
    ) is False


def test_message_store_renames_mailbox(
    message,
):
    store = MessageStore()

    entry = store.save_entry(
        "Archive",
        message,
    )

    store.add_flags(
        "Archive",
        entry.id,
        {
            "\\Seen",
        },
    )

    assert store.rename_mailbox(
        "Archive",
        "Old",
    ) is True

    assert store.list_mailboxes() == [
        "Old",
    ]

    assert store.list_entries(
        "Archive"
    ) == []

    renamed_entries = store.list_entries(
        "Old"
    )

    assert len(renamed_entries) == 1
    assert renamed_entries[0].id == entry.id
    assert renamed_entries[0].uid == entry.uid
    assert renamed_entries[0].flags == {
        "\\Seen",
    }


def test_message_store_rename_returns_false_for_missing_source():
    store = MessageStore()

    assert store.rename_mailbox(
        "Missing",
        "Archive",
    ) is False


def test_message_store_rename_returns_false_for_existing_destination():
    store = MessageStore()

    store.create_mailbox(
        "Archive"
    )

    store.create_mailbox(
        "Old"
    )

    assert store.rename_mailbox(
        "Archive",
        "Old",
    ) is False

    assert store.list_mailboxes() == [
        "Archive",
        "Old",
    ]


def test_message_store_manages_mailbox_subscriptions():
    store = MessageStore()

    store.create_mailbox(
        "Archive"
    )

    assert store.subscribe_mailbox(
        "Archive"
    ) is True

    assert store.list_subscribed_mailboxes() == [
        "Archive",
    ]

    assert store.unsubscribe_mailbox(
        "Archive"
    ) is True

    assert store.list_subscribed_mailboxes() == []


def test_message_store_rejects_subscription_to_missing_mailbox():
    store = MessageStore()

    assert store.subscribe_mailbox(
        "Missing"
    ) is False