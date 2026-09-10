# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0

# See LICENSE for the full license terms.


import json
from pathlib import Path
import stat

from garlicsmtp.security.auth.password_hasher import (
    PasswordHasher,
)


class ImapCredentialStore:

    def __init__(
        self,
        path: Path,
    ):
        self.path = path

    def create(
        self,
        *,
        username: str,
        password: str,
    ) -> None:
        if username != "garlicsmtp":
            raise ValueError(
                "IMAP username must be 'garlicsmtp'"
            )

        if self.path.exists():
            raise FileExistsError(
                self.path
            )

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        data = {
            "username": username,
            "password_hash": (
                PasswordHasher().hash_password(
                    password
                )
            ),
        }

        with self.path.open(
            "x",
            encoding="utf-8",
        ) as credentials_file:
            credentials_file.write(
                json.dumps(data)
            )

        self.path.chmod(0o600)

    def reset_password(
        self,
        *,
        password: str,
    ) -> None:
        if not self.path.exists():
            raise FileNotFoundError(
                self.path
            )

        file_stat = self.path.stat()

        mode = stat.S_IMODE(
            file_stat.st_mode
        )

        if mode != 0o600:
            raise PermissionError(
                "Insecure IMAP credentials permissions"
            )

        try:
            data = json.loads(
                self.path.read_text(
                    encoding="utf-8",
                )
            )
        except json.JSONDecodeError as exc:
            raise ValueError(
                "Invalid IMAP credentials"
            ) from exc

        if (
            "username" not in data
            or "password_hash" not in data
        ):
            raise ValueError(
                "Invalid IMAP credentials"
            )

        password_hash = data["password_hash"]

        if (
            not isinstance(
                password_hash,
                str,
            )
            or len(
                password_hash.split("$")
            ) != 7
            or not password_hash.startswith(
                "scrypt$"
            )
        ):
            raise ValueError(
                "Invalid IMAP credentials"
            )

        if data["username"] != "garlicsmtp":
            raise ValueError(
                "Invalid IMAP credentials"
            )

        data = {
            "username": "garlicsmtp",
            "password_hash": (
                PasswordHasher().hash_password(
                    password
                )
            ),
        }

        self.path.write_text(
            json.dumps(data),
            encoding="utf-8",
        )

        self.path.chmod(0o600)
