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
from garlicsmtp.security.auth.imap_credentials import (
    ImapCredentialStore,
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
        ImapCredentialStore(
            path=self.path,
        ).validate()

        data = json.loads(
            self.path.read_text(
                encoding="utf-8",
            )
        )

        if username != data["username"]:
            return False

        return PasswordHasher().verify_password(
            password,
            data["password_hash"],
        )
