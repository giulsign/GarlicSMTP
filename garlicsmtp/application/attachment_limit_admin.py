# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import json
from pathlib import Path

from garlicsmtp.application.attachment_limit import (
    ATTACHMENT_LIMIT_BYTES,
)
from garlicsmtp.security.auth.password_hasher import (
    PasswordHasher,
)


class AttachmentLimitAdminStore:

    def __init__(
        self,
        path: Path,
    ) -> None:
        self.path = path

    def create(
        self,
        *,
        password: str,
    ) -> None:
        if self.path.exists():
            raise FileExistsError(
                self.path
            )

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        data = {
            "limit_bytes": (
                ATTACHMENT_LIMIT_BYTES
            ),
            "password_hash": (
                PasswordHasher()
                .hash_password(
                    password
                )
            ),
        }

        with self.path.open(
            "x",
            encoding="utf-8",
        ) as config_file:
            config_file.write(
                json.dumps(data)
            )

        self.path.chmod(
            0o600
        )

    def change_limit(
        self,
        *,
        password: str,
        limit_bytes: int,
    ) -> None:
        if (
            isinstance(
                limit_bytes,
                bool,
            )
            or not isinstance(
                limit_bytes,
                int,
            )
            or limit_bytes <= 0
        ):
            raise ValueError(
                "limit_bytes must be a positive integer"
            )

        data = json.loads(
            self.path.read_text(
                encoding="utf-8"
            )
        )

        if not PasswordHasher().verify_password(
            password,
            data["password_hash"],
        ):
            raise PermissionError(
                "invalid password"
            )

        data["limit_bytes"] = limit_bytes

        self.path.write_text(
            json.dumps(data),
            encoding="utf-8",
        )
