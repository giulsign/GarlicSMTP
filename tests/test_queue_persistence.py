from garlicsmtp.queue.factory import QueueFactory
from garlicsmtp.queue.manager import QueueManager
from garlicsmtp.queue.sqlite import SQLiteQueueBackend


def test_queue_survives_restart(tmp_path, message):

    db = tmp_path / "queue.db"

    #
    # Prima istanza
    #

    queue = QueueManager(
        backend=SQLiteQueueBackend(db),
    )

    item = QueueFactory.create(message)

    queue.enqueue(item)

    assert queue.size() == 1

    #
    # Simula riavvio
    #

    queue = QueueManager(
        backend=SQLiteQueueBackend(db),
    )

    assert queue.size() == 1

    restored = queue.peek()

    assert restored is not None
    assert restored.id == item.id