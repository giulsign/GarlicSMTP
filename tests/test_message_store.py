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