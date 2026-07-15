from garlicsmtp.storage.memory.backend import (
    MemoryMessageStoreBackend,
)


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