from garlicsmtp.queue.item import QueueItem
from garlicsmtp.queue.storage import QueueStorage
from garlicsmtp.queue.manager import QueueManager
from garlicsmtp.queue.factory import QueueFactory


def test_queue_storage(tmp_path, message):

    storage = QueueStorage(tmp_path)

    item = QueueItem.create(

        "ABC123",

        message

    )

    storage.save(item)

    assert storage.exists("ABC123")

    restored = storage.load("ABC123")

    assert restored.id == item.id

    assert restored.message.envelope.sender == item.message.envelope.sender

    storage.delete("ABC123")

    assert not storage.exists("ABC123")

def test_queue_peek_returns_first_item(message):

    queue = QueueManager()

    item = QueueFactory.create(message)

    queue.enqueue(item)

    assert queue.peek() is item
    assert queue.size() == 1


def test_queue_peek_empty():

    queue = QueueManager()

    assert queue.peek() is None


def test_queue_ack_removes_peeked_item(message):

    queue = QueueManager()

    item = QueueFactory.create(message)

    queue.enqueue(item)

    assert queue.peek() is item
    assert queue.ack(item) is True
    assert queue.size() == 0


def test_queue_ack_wrong_item_does_not_remove(message):

    queue = QueueManager()

    item = QueueFactory.create(message)
    other = QueueFactory.create(message)

    queue.enqueue(item)

    assert queue.ack(other) is False
    assert queue.size() == 1
    assert queue.peek() is item
