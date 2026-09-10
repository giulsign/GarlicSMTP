# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0

# See LICENSE for the full license terms.


import json

import stat 

from pathlib import Path

from garlicsmtp.security.auth.authenticator import (
    Authenticator,
)
from garlicsmtp.security.auth.password_hasher import (
    PasswordHasher,
)


class PersistentImapAuthenticator(
    Authenticator,
):

    def __init__(
        self,
        path: Path,
    ):
        self.path = path

    def authenticate(
        self,
        username: str,
        password: str,
    ) -> bool:
        file_stat = self.path.lstat()

        if stat.S_ISLNK(
            file_stat.st_mode
        ):
            raise ValueError(
                "Invalid IMAP credentials"
            )

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

        if data["username"] != "garlicsmtp":
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

        if username != data["username"]:
            return False

        return PasswordHasher().verify_password(
            password,
            password_hash,
        )
