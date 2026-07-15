import sqlite3
import threading
from datetime import UTC, datetime
from uuid import uuid4

from garlicsmtp.models import MailMessage
from garlicsmtp.storage.backend import (
    MessageStoreBackend,
)
from garlicsmtp.storage.serializer import (
    MessageSerializer,
)


class SQLiteMessageStoreBackend(
    MessageStoreBackend
):

    def __init__(self, path):
        self.path = path
        self._lock = threading.RLock()

        self.connection = sqlite3.connect(
            path,
            check_same_thread=False,
        )

        self._create_schema()

    def _create_schema(self) -> None:
        with self._lock:
            self.connection.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    mailbox TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created TEXT NOT NULL
                )
                """
            )

            self.connection.commit()

    def save(
        self,
        mailbox: str,
        message: MailMessage,
    ) -> str:
        message_id = str(uuid4())

        with self._lock:
            self.connection.execute(
                """
                INSERT INTO messages (
                    id,
                    mailbox,
                    payload,
                    created
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    message_id,
                    mailbox,
                    MessageSerializer.to_json(
                        message
                    ),
                    datetime.now(
                        UTC
                    ).isoformat(),
                ),
            )

            self.connection.commit()

        return message_id

    def list_messages(
        self,
        mailbox: str,
    ) -> list[str]:
        with self._lock:
            rows = self.connection.execute(
                """
                SELECT id
                FROM messages
                WHERE mailbox = ?
                ORDER BY created ASC
                """,
                (mailbox,),
            ).fetchall()

        return [
            row[0]
            for row in rows
        ]

    def get(
        self,
        mailbox: str,
        message_id: str,
    ) -> MailMessage | None:
        with self._lock:
            row = self.connection.execute(
                """
                SELECT payload
                FROM messages
                WHERE mailbox = ?
                  AND id = ?
                """,
                (
                    mailbox,
                    message_id,
                ),
            ).fetchone()

        if row is None:
            return None

        return MessageSerializer.from_json(
            row[0]
        )

    def close(self) -> None:
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


    def list_mailboxes(self) -> list[str]:
        with self._lock:
            rows = self.connection.execute(
                """
                SELECT DISTINCT mailbox
                FROM messages
                ORDER BY mailbox ASC
                """
            ).fetchall()

        return [
            row[0]
            for row in rows
        ]


    def count(self, mailbox: str) -> int:
        with self._lock:
            row = self.connection.execute(
                """
                SELECT COUNT(*)
                FROM messages
                WHERE mailbox = ?
                """,
                (mailbox,),
            ).fetchone()

        return row[0]