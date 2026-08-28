# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

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
import json
from garlicsmtp.storage.entry import MessageEntry


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
                CREATE TABLE IF NOT EXISTS mailboxes (
                    name TEXT PRIMARY KEY
                )
                """
            )

            self.connection.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    mailbox TEXT NOT NULL,
                    uid INTEGER,
                    payload TEXT NOT NULL,
                    internal_date TEXT,
                    flags TEXT,
                    created TEXT NOT NULL
                )
                """
            )

            self._migrate_schema()

            self.connection.execute(
                """
                INSERT OR IGNORE INTO mailboxes (name)
                SELECT DISTINCT mailbox
                FROM messages
                """
            )

            self._migrate_mailbox_schema()

            self.connection.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS
                idx_messages_mailbox_uid
                ON messages (mailbox, uid)
                """
            )

            self.connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_messages_mailbox
                ON messages (mailbox)
                """
            )

            self.connection.execute(
                """
                CREATE TABLE IF NOT EXISTS mailbox_subscriptions (
                    mailbox TEXT PRIMARY KEY
                )
                """
            )

            self.connection.commit()


    def _migrate_schema(self) -> None:
        columns = {
            row[1]
            for row in self.connection.execute(
                "PRAGMA table_info(messages)"
            ).fetchall()
        }

        if "uid" not in columns:
            self.connection.execute(
                """
                ALTER TABLE messages
                ADD COLUMN uid INTEGER
                """
            )

        if "internal_date" not in columns:
            self.connection.execute(
                """
                ALTER TABLE messages
                ADD COLUMN internal_date TEXT
                """
            )

        if "flags" not in columns:
            self.connection.execute(
                """
                ALTER TABLE messages
                ADD COLUMN flags TEXT
                """
            )

        self._populate_missing_entry_fields()


    def save(
        self,
        mailbox: str,
        message: MailMessage,
    ) -> str:
        entry = self.save_entry(
            mailbox,
            message,
        )

        return entry.id

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
        entry = self.get_entry(
            mailbox,
            message_id,
        )

        if entry is None:
            return None

        return entry.message

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
                SELECT name
                FROM mailboxes
                ORDER BY name ASC
                """
            ).fetchall()

        return [
            row[0]
            for row in rows
        ]

    def create_mailbox(
        self,
        mailbox: str,
    ) -> bool:
        with self._lock:
            row = self.connection.execute(
                """
                SELECT 1
                FROM mailboxes
                WHERE name = ?
                """,
                (
                    mailbox,
                ),
            ).fetchone()

            if row is not None:
                return False

            uid_validity = (
                self._allocate_uid_validity()
            )

            self.connection.execute(
                """
                INSERT INTO mailboxes (
                    name,
                    uid_validity
                )
                VALUES (?, ?)
                """,
                (
                    mailbox,
                    uid_validity,
                ),
            )

            self.connection.commit()

            return True

    def delete_mailbox(
        self,
        mailbox: str,
    ) -> bool:
        with self._lock:
            row = self.connection.execute(
                """
                SELECT 1
                FROM mailboxes
                WHERE name = ?
                """,
                (mailbox,),
            ).fetchone()

            if row is None:
                return False

            self.connection.execute(
                """
                DELETE FROM mailbox_subscriptions
                WHERE mailbox = ?
                """,
                (mailbox,),
            )

            self.connection.execute(
                """
                DELETE FROM mailboxes
                WHERE name = ?
                """,
                (mailbox,),
            )

            self.connection.execute(
                """
                DELETE FROM messages
                WHERE mailbox = ?
                """,
                (mailbox,),
            )

            self.connection.commit()

            return True
        
    def rename_mailbox(
        self,   
        source: str,
        destination: str,
    ) -> bool:
        with self._lock:
            source_row = self.connection.execute(
                """
                SELECT 1
                FROM mailboxes
                WHERE name = ?
                """,
                (source,),
            ).fetchone()

            if source_row is None:
                return False

            destination_row = self.connection.execute(
                """
                SELECT 1
                FROM mailboxes
                WHERE name = ?
                """,
                (destination,),
            ).fetchone()

            if destination_row is not None:
                return False

            self.connection.execute(
                """
                UPDATE mailboxes
                SET name = ?
                WHERE name = ?
                """,
                (
                    destination,
                    source,
                ),
            )

            self.connection.execute(
                """
                UPDATE messages
                SET mailbox = ?
                WHERE mailbox = ?
                """,
                (
                    destination,
                    source,
                ),
            )

            self.connection.execute(
                """
                UPDATE mailbox_subscriptions
                SET mailbox = ?
                WHERE mailbox = ?
                """,
                (
                    destination,
                    source,
                ),
            )

            self.connection.commit()

            return True

    def subscribe_mailbox(
        self,
        mailbox: str,
    ) -> bool:
        with self._lock:
            row = self.connection.execute(
                """
                SELECT 1
                FROM mailboxes
                WHERE name = ?
                """,
                (mailbox,),
            ).fetchone()

            if row is None:
                return False

            self.connection.execute(
                """
                INSERT OR IGNORE INTO mailbox_subscriptions (
                    mailbox
                )
                VALUES (?)
                """,
                (mailbox,),
            )

            self.connection.commit()

            return True

    def unsubscribe_mailbox(
        self,
        mailbox: str,
    ) -> bool:
        with self._lock:
            cursor = self.connection.execute(
                """
                DELETE FROM mailbox_subscriptions
                WHERE mailbox = ?
                """,
                (mailbox,),
            )

            if cursor.rowcount != 1:
                self.connection.rollback()
                return False

            self.connection.commit()

            return True

    def list_subscribed_mailboxes(
        self,
    ) -> list[str]:
        with self._lock:
            rows = self.connection.execute(
                """
                SELECT mailbox
                FROM mailbox_subscriptions
                ORDER BY mailbox
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
        

    def _populate_missing_entry_fields(self) -> None:
        mailboxes = self.connection.execute(
            """
            SELECT DISTINCT mailbox
            FROM messages
            """
        ).fetchall()

        for (mailbox,) in mailboxes:    
            rows = self.connection.execute(
                """
                SELECT id, uid, internal_date, flags, created
                FROM messages
                WHERE mailbox = ?
                ORDER BY created ASC, rowid ASC
                """,
                (mailbox,),
            ).fetchall()

            used_uids = {
                uid
                for _, uid, _, _, _ in rows
                if uid is not None
            }

            next_uid = max(
                used_uids,
                default=0,
            ) + 1

            for (
                message_id,
                uid,
                internal_date,
                flags,
                created,
            ) in rows:
                if uid is None:
                    while next_uid in used_uids:
                        next_uid += 1

                    uid = next_uid
                    used_uids.add(uid)
                    next_uid += 1

                if internal_date is None:
                    internal_date = created

                if flags is None:
                    flags = json.dumps([])

                self.connection.execute(
                    """
                    UPDATE messages
                    SET uid = ?,
                        internal_date = ?,
                        flags = ?
                    WHERE id = ?
                    """,
                    (
                        uid,
                        internal_date,
                        flags,
                        message_id,
                    ),
                )

    def _ensure_mailbox(
        self,
        mailbox: str,
    ) -> None:
        row = self.connection.execute(
            """
            SELECT 1
            FROM mailboxes
            WHERE name = ?
            """,
            (
                mailbox,
            ),
        ).fetchone()

        if row is not None:
            return

        uid_validity = (
            self._allocate_uid_validity()
        )

        self.connection.execute(
            """
            INSERT INTO mailboxes (
                name,
                uid_validity
            )
            VALUES (?, ?)
            """,
            (
                mailbox,
                uid_validity,
            ),
        )

    def _next_uid(
        self,
        mailbox: str,
    ) -> int:
        row = self.connection.execute(
            """
            SELECT COALESCE(MAX(uid), 0)
            FROM messages
            WHERE mailbox = ?
            """,
            (mailbox,),
        ).fetchone()

        return int(row[0]) + 1
    

    def save_entry(
        self,
        mailbox: str,
        message: MailMessage,
    ) -> MessageEntry:
        message_id = str(uuid4())
        internal_date = datetime.now(UTC)
        flags = set()

        with self._lock:
            self._ensure_mailbox(
                mailbox
            )

            uid = self._next_uid(mailbox)

            self.connection.execute(
                """
                INSERT INTO messages (
                    id,
                    mailbox,
                    uid,
                    payload,
                    internal_date,
                    flags,
                    created
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    message_id,
                    mailbox,
                    uid,
                    MessageSerializer.to_json(message),
                    internal_date.isoformat(),
                    json.dumps(sorted(flags)),
                    internal_date.isoformat(),
                ),
            )

            self.connection.commit()

        return MessageEntry(
            id=message_id,
            mailbox=mailbox,
            uid=uid,
            message=message,
            internal_date=internal_date,
            flags=flags,
        )
    
    def append_entry(
        self,
        mailbox: str,
        message: MailMessage,
        flags: set[str],
        internal_date: datetime,
    ) -> MessageEntry:
        message_id = str(uuid4())
        stored_flags = set(flags)
        created = datetime.now(UTC)

        with self._lock:
            self._ensure_mailbox(
                mailbox
            )
            uid = self._next_uid(
                mailbox
            )

            self.connection.execute(
                """
                INSERT INTO messages (
                    id,
                    mailbox,
                    uid,
                    payload,
                    internal_date,
                    flags,
                    created
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    message_id,
                    mailbox,
                    uid,
                    MessageSerializer.to_json(
                        message
                    ),
                    internal_date.isoformat(),
                    json.dumps(
                        sorted(stored_flags)
                    ),
                    created.isoformat(),
                ),
            )

            self.connection.commit()

        return MessageEntry(
            id=message_id,
            mailbox=mailbox,
            uid=uid,
            message=message,
            internal_date=internal_date,
            flags=stored_flags,
        )

    def get_entry(
        self,
        mailbox: str,
        message_id: str,
    ) -> MessageEntry | None:
        with self._lock:
            row = self.connection.execute(
                """
                SELECT
                    id,
                    mailbox,
                    uid,
                    payload,
                    internal_date,
                    flags
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

        (
            stored_id,
            stored_mailbox,
            uid,
            payload,
            internal_date,
            flags,
        ) = row

        return MessageEntry(
            id=stored_id,
            mailbox=stored_mailbox,
            uid=uid,
            message=MessageSerializer.from_json(
                payload
            ),
            internal_date=datetime.fromisoformat(
                internal_date
            ),
            flags=set(
                json.loads(flags)
            ),
        )
    

    def list_entries(
        self,
        mailbox: str,
    ) -> list[MessageEntry]:
        with self._lock:
            rows = self.connection.execute(
                """
                SELECT
                    id,
                    mailbox,
                    uid,
                    payload,
                    internal_date,
                    flags
                FROM messages
                WHERE mailbox = ?
                ORDER BY uid ASC
                """,
                (mailbox,),
            ).fetchall()

        return [
            MessageEntry(
                id=message_id,
                mailbox=stored_mailbox,
                uid=uid,
                message=MessageSerializer.from_json(
                    payload
                ),
                internal_date=datetime.fromisoformat(
                    internal_date
                ),
                flags=set(
                    json.loads(flags)
                ),
            )
            for (
                message_id,
                stored_mailbox,
                uid,
                payload,
                internal_date,
                flags,
            ) in rows
        ]
    
    def set_flags(
        self,
        mailbox: str,
        message_id: str,
        flags: set[str],
    ) -> bool:
        with self._lock:
            cursor = self.connection.execute(
                """
                UPDATE messages
                SET flags = ?
                WHERE mailbox = ?
                AND id = ?
                """,
                (
                    json.dumps(
                        sorted(flags)
                    ),
                    mailbox,
                    message_id,
                ),
            )

            self.connection.commit()

            return cursor.rowcount == 1
        

    def add_flags(
        self,
        mailbox: str,
        message_id: str,
        flags: set[str],
    ) -> bool:
        entry = self.get_entry(
            mailbox,
            message_id,
        )

        if entry is None:
            return False

        return self.set_flags(
            mailbox,
            message_id,
            entry.flags | flags,
        )


    def remove_flags(
        self,
        mailbox: str,
        message_id: str,
        flags: set[str],
    ) -> bool:
        entry = self.get_entry(
            mailbox,
            message_id,
        )

        if entry is None:
            return False

        return self.set_flags(
            mailbox,
            message_id,
            entry.flags - flags,
        )
    
    def copy_entry(
        self,
        source_mailbox: str,
        message_id: str,
        destination_mailbox: str,
    ) -> MessageEntry | None:
        source = self.get_entry(
            source_mailbox,
            message_id,
        )

        if source is None:
            return None

        copied_id = str(uuid4())

        with self._lock:
            self._ensure_mailbox(   
                destination_mailbox
            )
            copied_uid = self._next_uid(
                destination_mailbox
            )

            self.connection.execute(
                """
                INSERT INTO messages (
                    id,
                    mailbox,
                    uid,
                    payload,
                    internal_date,
                    flags,
                    created
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    copied_id,
                    destination_mailbox,
                    copied_uid,
                    MessageSerializer.to_json(
                        source.message
                    ),
                    source.internal_date.isoformat(),
                    json.dumps(
                        sorted(source.flags)
                    ),
                    source.internal_date.isoformat(),
                ),
            )

            self.connection.commit()

        return MessageEntry(
            id=copied_id,
            mailbox=destination_mailbox,
            uid=copied_uid,
            message=source.message,
            internal_date=source.internal_date,
            flags=set(source.flags),
        )

    def delete_entry(
        self,
        mailbox: str,
        message_id: str,
    ) -> bool:
        with self._lock:
            cursor = self.connection.execute(
                """
                DELETE FROM messages
                WHERE mailbox = ?
                AND id = ?
                """,
                (
                    mailbox,
                    message_id,
                ),
            )

            self.connection.commit()

            return cursor.rowcount == 1

    def get_uid_validity(
        self,
        mailbox: str,
    ) -> int:
        with self._lock:
            row = self.connection.execute(
                """
                SELECT uid_validity
                FROM mailboxes
                WHERE name = ?
                """,
                (
                    mailbox,
                ),
            ).fetchone()

        if (
            row is None
            or row[0] is None
        ):
            raise KeyError(
                f"Mailbox not found: {mailbox}"
            )

        return int(
            row[0]
        )

    def _migrate_mailbox_schema(
        self,
    ) -> None:
        columns = {
            row[1]
            for row in self.connection.execute(
                "PRAGMA table_info(mailboxes)"
            ).fetchall()
        }

        if "uid_validity" not in columns:
            self.connection.execute(
                """
                ALTER TABLE mailboxes
                ADD COLUMN uid_validity INTEGER
                """
            )

        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS storage_metadata (
                key TEXT PRIMARY KEY,
                value INTEGER NOT NULL
            )
            """
        )

        row = self.connection.execute(
            """
            SELECT value
            FROM storage_metadata
            WHERE key = 'next_uid_validity'
            """
        ).fetchone()

        if row is None:
            max_row = self.connection.execute(
                """
                SELECT COALESCE(
                    MAX(uid_validity),
                    0
                )
                FROM mailboxes
                """
            ).fetchone()

            next_uid_validity = (
                int(max_row[0]) + 1
            )

            self.connection.execute(
                """
                INSERT INTO storage_metadata (
                    key,
                    value
                )
                VALUES (
                    'next_uid_validity',
                    ?
                )
                """,
                (
                    next_uid_validity,
                ),
            )

        rows = self.connection.execute(
            """
            SELECT name
            FROM mailboxes
            WHERE uid_validity IS NULL
            ORDER BY name
            """
        ).fetchall()

        for (mailbox,) in rows:
            uid_validity = (
                self._allocate_uid_validity()
            )

            self.connection.execute(
                """
                UPDATE mailboxes
                SET uid_validity = ?
                WHERE name = ?
                """,
                (
                    uid_validity,
                    mailbox,
                ),
            )

    def _allocate_uid_validity(
        self,
    ) -> int:
        row = self.connection.execute(
            """
            SELECT value
            FROM storage_metadata
            WHERE key = 'next_uid_validity'
            """
        ).fetchone()

        if row is None:
            uid_validity = 1

            self.connection.execute(
                """
                INSERT INTO storage_metadata (
                    key,
                    value
                )
                VALUES (
                    'next_uid_validity',
                    2
                )
                """
            )

            return uid_validity

        uid_validity = int(
            row[0]
        )

        self.connection.execute(
            """
            UPDATE storage_metadata
            SET value = ?
            WHERE key = 'next_uid_validity'
            """,
            (
                uid_validity + 1,
            ),
        )

        return uid_validity