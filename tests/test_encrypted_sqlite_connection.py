import sqlite3

import pytest

from garlicsmtp.security.encrypted_sqlite import (
    connect_encrypted_sqlite,
)
from sqlcipher3 import dbapi2 as sqlcipher


def test_encrypted_sqlite_database_is_not_readable_without_dek(
    tmp_path,
):
    database = tmp_path / "protected.db"
    dek = bytes(range(32))

    connection = connect_encrypted_sqlite(
        database,
        dek=dek,
    )

    try:
        connection.execute(
            "CREATE TABLE secrets (value TEXT NOT NULL)"
        )
        connection.execute(
            "INSERT INTO secrets (value) VALUES (?)",
            ("GARLICSMTP_SECRET_SENTINEL",),
        )
        connection.commit()
    finally:
        connection.close()

    raw_bytes = database.read_bytes()

    assert not raw_bytes.startswith(b"SQLite format 3\x00")
    assert b"GARLICSMTP_SECRET_SENTINEL" not in raw_bytes

    # Una connessione SQLite standard non deve poter leggere il DB.
    with sqlite3.connect(database) as plaintext_connection:
        with pytest.raises(sqlite3.DatabaseError):
            plaintext_connection.execute(
                "SELECT value FROM secrets"
            ).fetchall()

    # La DEK corretta deve consentire la riapertura.
    restored = connect_encrypted_sqlite(
        database,
        dek=dek,
    )

    try:
        assert restored.execute(
            "SELECT value FROM secrets"
        ).fetchone() == (
            "GARLICSMTP_SECRET_SENTINEL",
        )
    finally:
        restored.close()


def test_encrypted_sqlite_rejects_wrong_dek(tmp_path):
    database = tmp_path / "protected.db"

    connection = connect_encrypted_sqlite(
        database,
        dek=bytes(range(32)),
    )
    try:
        connection.execute(
            "CREATE TABLE secrets (value TEXT NOT NULL)"
        )
        connection.commit()
    finally:
        connection.close()

    with pytest.raises(sqlcipher.DatabaseError):
        connect_encrypted_sqlite(
            database,
            dek=bytes(reversed(range(32))),
        )


def test_encrypted_sqlite_rejects_plaintext_database(tmp_path):
    database = tmp_path / "plaintext.db"

    with sqlite3.connect(database) as connection:
        connection.execute(
            "CREATE TABLE secrets (value TEXT NOT NULL)"
        )
        connection.execute(
            "INSERT INTO secrets (value) VALUES (?)",
            ("GARLICSMTP_PLAINTEXT_SECRET",),
        )

    original_bytes = database.read_bytes()

    with pytest.raises(sqlcipher.DatabaseError):
        connect_encrypted_sqlite(
            database,
            dek=bytes(range(32)),
        )

    assert database.read_bytes() == original_bytes


def test_encrypted_sqlite_wal_does_not_expose_payload(tmp_path):
    database = tmp_path / "protected.db"
    sentinel = b"GARLICSMTP_WAL_SECRET"

    connection = connect_encrypted_sqlite(
        database,
        dek=bytes(range(32)),
    )

    try:
        mode = connection.execute(
            "PRAGMA journal_mode=WAL"
        ).fetchone()[0]

        assert mode.lower() == "wal"

        connection.execute(
            "CREATE TABLE secrets (value TEXT NOT NULL)"
        )
        connection.commit()

        connection.execute(
            "INSERT INTO secrets (value) VALUES (?)",
            (sentinel.decode(),),
        )
        connection.commit()

        wal = tmp_path / "protected.db-wal"
        assert wal.is_file()

        for path in (database, wal):
            assert sentinel not in path.read_bytes()
    finally:
        connection.close()


def test_encrypted_sqlite_rollback_journal_does_not_expose_payload(
    tmp_path,
):
    database = tmp_path / "protected.db"
    sentinel = b"GARLICSMTP_JOURNAL_SECRET"

    connection = connect_encrypted_sqlite(
        database,
        dek=bytes(range(32)),
    )

    try:
        mode = connection.execute(
            "PRAGMA journal_mode=DELETE"
        ).fetchone()[0]

        assert mode.lower() == "delete"

        connection.execute(
            "CREATE TABLE secrets (value TEXT NOT NULL)"
        )
        connection.execute(
            "INSERT INTO secrets (value) VALUES (?)",
            (sentinel.decode(),),
        )
        connection.commit()

        connection.execute("BEGIN IMMEDIATE")
        connection.execute(
            "UPDATE secrets SET value = ?",
            ("GARLICSMTP_UPDATED_SECRET",),
        )

        journal = tmp_path / "protected.db-journal"
        assert journal.is_file()

        journal_bytes = journal.read_bytes()

        assert sentinel not in journal_bytes
        assert b"GARLICSMTP_UPDATED_SECRET" not in journal_bytes

        connection.rollback()
    finally:
        connection.close()


def test_encrypted_sqlite_uses_memory_for_temporary_storage(tmp_path):
    database = tmp_path / "protected.db"

    connection = connect_encrypted_sqlite(
        database,
        dek=bytes(range(32)),
    )

    try:
        mode = connection.execute(
            "PRAGMA temp_store"
        ).fetchone()[0]

        assert mode == 2
    finally:
        connection.close()


@pytest.mark.parametrize(
    "invalid_dek",
    [
        None,
        b"",
        b"\x00" * 16,
        b"\x00" * 31,
        b"\x00" * 33,
        "not-a-binary-key",
    ],
)
def test_encrypted_sqlite_rejects_invalid_dek_without_creating_file(
    tmp_path,
    invalid_dek,
):
    database = tmp_path / "protected.db"

    with pytest.raises(ValueError):
        connect_encrypted_sqlite(
            database,
            dek=invalid_dek,
        )

    assert not database.exists()