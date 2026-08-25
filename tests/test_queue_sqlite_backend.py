from garlicsmtp.queue.factory import QueueFactory
from garlicsmtp.queue.sqlite import SQLiteQueueBackend
from datetime import UTC, datetime, timedelta
import threading

def test_sqlite_queue_persists_items(tmp_path, message):

    db_path = tmp_path / "queue.db"

    backend = SQLiteQueueBackend(db_path)

    item = QueueFactory.create(message)

    backend.enqueue(item)

    assert backend.size() == 1

    restored = SQLiteQueueBackend(db_path)

    assert restored.size() == 1
    assert restored.peek().id == item.id


def test_sqlite_queue_ack_removes_item(tmp_path, message):

    db_path = tmp_path / "queue.db"

    backend = SQLiteQueueBackend(db_path)

    item = QueueFactory.create(message)

    backend.enqueue(item)

    assert backend.size() == 1

    assert backend.ack(item) is True

    assert backend.size() == 0
    assert backend.peek() is None


def test_sqlite_queue_nack_keeps_item(tmp_path, message):

    db_path = tmp_path / "queue.db"

    backend = SQLiteQueueBackend(db_path)

    item = QueueFactory.create(message)

    backend.enqueue(item)

    backend.nack(item)

    assert backend.size() == 1
    assert backend.peek().id == item.id


def test_sqlite_queue_empty(tmp_path):

    db_path = tmp_path / "queue.db"

    backend = SQLiteQueueBackend(db_path)

    assert backend.empty() is True
    assert backend.size() == 0


def test_sqlite_backend_can_be_closed(tmp_path):

    backend = SQLiteQueueBackend(
        tmp_path / "queue.db"
    )

    backend.close()


def test_sqlite_queue_update_persists_changes(tmp_path, message):

    db_path = tmp_path / "queue.db"

    backend = SQLiteQueueBackend(db_path)

    item = QueueFactory.create(message)

    backend.enqueue(item)

    item.attempts = 2
    item.next_retry = datetime(2026, 1, 1, tzinfo=UTC)
    item.last_error = "temporary failure"

    assert backend.update(item) is True

    restored = SQLiteQueueBackend(db_path)

    saved = restored.peek()

    assert saved.attempts == 2
    assert saved.next_retry == datetime(2026, 1, 1, tzinfo=UTC)
    assert saved.last_error == "temporary failure"


def test_sqlite_queue_can_enqueue_from_another_thread(
    tmp_path,
    message,
):
    backend = SQLiteQueueBackend(
        tmp_path / "queue.db"
    )

    item = QueueFactory.create(message)
    errors = []

    def enqueue():
        try:
            backend.enqueue(item)
        except Exception as exc:
            errors.append(exc)

    thread = threading.Thread(
        target=enqueue,
    )

    thread.start()
    thread.join(timeout=2)

    assert thread.is_alive() is False
    assert errors == []
    assert backend.size() == 1


def test_sqlite_queue_peek_skips_not_ready_item(
    tmp_path,
    message,
):
    backend = SQLiteQueueBackend(
        tmp_path / "queue.db"
    )

    first = QueueFactory.create(
        message
    )

    first.next_retry = (
        datetime.now(UTC)
        + timedelta(hours=1)
    )

    second = QueueFactory.create(
        message
    )

    second.next_retry = None

    backend.enqueue(first)
    backend.enqueue(second)

    item = backend.peek()

    assert item is not None
    assert item.id == second.id


