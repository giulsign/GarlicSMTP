# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import json
from pathlib import Path
import stat

from garlicsmtp.security.auth.password_hasher import (
    PasswordHasher,
)


class AccountCredentialStore:

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
        if not username.strip():
            raise ValueError(
                "Account username is required"
            )

        if len(password) < 8:
            raise ValueError(
                "Account password must be at least 8 characters"
            )

        if not any(
            character.isupper()
            for character in password
        ):
            raise ValueError(
                "Account password must contain an uppercase letter"
            )

        if not any(
            character.isdigit()
            for character in password
        ):
            raise ValueError(
                "Account password must contain a digit"
            )

        if not any(
            not character.isalnum()
            for character in password
        ):
            raise ValueError(
                "Account password must contain a special character"
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

    def validate(
        self,
    ) -> None:

        file_stat = self.path.lstat()

        if stat.S_ISLNK(
            file_stat.st_mode
        ):
            raise ValueError(
                "Invalid account credentials"
            )

        mode = stat.S_IMODE(
            file_stat.st_mode
        )

        if mode != 0o600:
            raise PermissionError(
                "Insecure account credentials permissions"
            )

        try:
            data = json.loads(
                self.path.read_text(
                    encoding="utf-8",
                )
            )
        except json.JSONDecodeError as exc:
            raise ValueError(
                "Invalid account credentials"
            ) from exc

        if (
            "username" not in data
            or "password_hash" not in data
        ):
            raise ValueError(
                "Invalid account credentials"
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
                "Invalid account credentials"
            )

    def authenticate(
        self,
        *,
        username: str,
        password: str,
    ) -> bool:
        self.validate()
        data = json.loads(
            self.path.read_text(
                encoding="utf-8",
            )
        )

        if data["username"] != username:
            return False

        return PasswordHasher().verify_password(
            password,
            data["password_hash"],
        )
