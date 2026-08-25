import sqlite3
import threading

from garlicsmtp.queue.backend import QueueBackend
from garlicsmtp.queue.serializer import QueueSerializer


class SQLiteQueueBackend(QueueBackend):

    def __init__(self, path):
        self.path = path
        self._lock = threading.RLock()

        self.connection = sqlite3.connect(
            self.path,
            check_same_thread=False,
        )

        self._create_schema()

    def _create_schema(self):
        with self._lock:
            self.connection.execute(
                """
                CREATE TABLE IF NOT EXISTS queue_items (
                    id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL
                )
                """
            )
            self.connection.commit()

    def enqueue(self, item):
        with self._lock:
            self.connection.execute(
                """
                INSERT INTO queue_items (id, payload)
                VALUES (?, ?)
                """,
                (
                    item.id,
                    QueueSerializer.to_json(item),
                ),
            )
            self.connection.commit()

    def peek(self):
        with self._lock:
            rows = self.connection.execute(
                """
                SELECT payload
                FROM queue_items
                ORDER BY rowid ASC
                """
            ).fetchall()

        for row in rows:
            item = QueueSerializer.from_json(
                row[0]
            )

            if item.ready():
                return item

        return None

    def ack(self, item):
        with self._lock:
            cursor = self.connection.execute(
                """
                DELETE FROM queue_items
                WHERE id = ?
                """,
                (item.id,),
            )
            self.connection.commit()

            return cursor.rowcount == 1

    def nack(self, item):
        return True

    def update(self, item):
        with self._lock:
            cursor = self.connection.execute(
                """
                UPDATE queue_items
                SET payload = ?
                WHERE id = ?
                """,
                (
                    QueueSerializer.to_json(item),
                    item.id,
                ),
            )
            self.connection.commit()

            return cursor.rowcount == 1

    def dequeue(self):
        with self._lock:
            item = self.peek()

            if item is None:
                return None

            self.ack(item)

            return item

    def size(self):
        with self._lock:
            row = self.connection.execute(
                """
                SELECT COUNT(*)
                FROM queue_items
                """
            ).fetchone()

            return row[0]

    def empty(self):
        return self.size() == 0

    def close(self):
        with self._lock:
            self.connection.close()

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type,
        exc,
        traceback,
    ):
        self.close()