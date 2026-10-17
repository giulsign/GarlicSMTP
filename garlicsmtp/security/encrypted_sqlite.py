from pathlib import Path

from sqlcipher3 import dbapi2 as sqlcipher


def connect_encrypted_sqlite(
    path: str | Path,
    *,
    dek: bytes,
):
    if not isinstance(dek, bytes) or len(dek) != 32:
        raise ValueError("DEK must be exactly 32 bytes")

    connection = sqlcipher.connect(
        str(path),
        check_same_thread=False,
    )

    try:
        version = connection.execute(
            "PRAGMA cipher_version"
        ).fetchone()

        if version is None or not version[0]:
            raise RuntimeError(
                "SQLCipher encryption is unavailable"
            )

        # SQLCipher raw key: 32 byte rappresentati
        # da 64 caratteri esadecimali.
        connection.execute(
            f"PRAGMA key = \"x'{dek.hex()}'\""
        )

        connection.execute(
            "PRAGMA temp_store=MEMORY"
        )

        connection.execute(
            "SELECT count(*) FROM sqlite_master"
        ).fetchone()

        return connection

    except Exception:
        connection.close()
        raise
