import pytest

from garlicsmtp.storage.sqlite.backend import (
    SQLiteMessageStoreBackend,
)
from garlicsmtp.queue.sqlite import SQLiteQueueBackend


@pytest.mark.parametrize(
    "backend_class",
    [
        SQLiteMessageStoreBackend,
        SQLiteQueueBackend,
    ],
)
def test_sqlite_backend_requires_dek_before_creating_database(
    tmp_path,
    backend_class,
):
    database = tmp_path / "protected.db"

    with pytest.raises((TypeError, ValueError)):
        backend_class(database)

    assert not database.exists()


import sqlite3

from sqlcipher3 import dbapi2 as sqlcipher


@pytest.mark.parametrize(
    "backend_class, table_name",
    [
        (SQLiteMessageStoreBackend, "messages"),
        (SQLiteQueueBackend, "queue_items"),
    ],
)
def test_sqlite_backend_encrypts_and_reopens_database(
    tmp_path,
    backend_class,
    table_name,
):
    database = tmp_path / "protected.db"
    dek = bytes(range(32))
    sentinel = "GARLICSMTP_BACKEND_SECRET"

    backend = backend_class(database, dek=dek)

    try:
        backend.connection.execute(
            f"INSERT INTO {table_name} "
            "(id, payload"
            + (", mailbox, created" if table_name == "messages" else "")
            + ") VALUES (?, ?"
            + (", ?, ?" if table_name == "messages" else "")
            + ")",
            (
                ("test-message", sentinel, "INBOX", "2026-01-01T00:00:00")
                if table_name == "messages"
                else ("test-item", sentinel)
            ),
        )
        backend.connection.commit()
    finally:
        backend.close()

    raw_bytes = database.read_bytes()

    assert not raw_bytes.startswith(b"SQLite format 3\x00")
    assert sentinel.encode() not in raw_bytes

    with sqlite3.connect(database) as plaintext_connection:
        with pytest.raises(sqlite3.DatabaseError):
            plaintext_connection.execute(
                f"SELECT payload FROM {table_name}"
            ).fetchall()

    reopened = backend_class(database, dek=dek)

    try:
        row = reopened.connection.execute(
            f"SELECT payload FROM {table_name} WHERE id = ?",
            ("test-message" if table_name == "messages" else "test-item",),
        ).fetchone()

        assert row == (sentinel,)
    finally:
        reopened.close()