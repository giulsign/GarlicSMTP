# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from pathlib import Path
import os
import tempfile

from cryptography.hazmat.primitives import (
    serialization,
)
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)


class SigningIdentity:

    def __init__(
        self,
        path: Path,
    ):
        self.path = Path(path)
        self._reject_symlink()
        self.private_key = self._load_or_create()

    def _load_or_create(
        self,
    ) -> Ed25519PrivateKey:
        if self.path.exists():
            return self._load()

        private_key = Ed25519PrivateKey.generate()

        self._save(
            private_key
        )

        return private_key

    def _load(
        self,
    ) -> Ed25519PrivateKey:
        raw = self.path.read_bytes()

        return Ed25519PrivateKey.from_private_bytes(
            raw
        )

    def _save(
        self,
        private_key: Ed25519PrivateKey,
    ) -> None:
        self._reject_symlink()

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.path.parent.chmod(
            0o700
        )

        raw = private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )

        fd, temporary_name = tempfile.mkstemp(
            dir=self.path.parent,
            prefix=f".{self.path.name}.",
            suffix=".tmp",
        )

        temporary_path = Path(
            temporary_name
        )

        try:
            os.chmod(
                temporary_path,
                0o600,
            )

            with os.fdopen(
                fd,
                "wb",
            ) as handle:
                handle.write(
                    raw
                )

                handle.flush()

                os.fsync(
                    handle.fileno()
                )

            os.replace(
                temporary_path,
                self.path,
            )

            self.path.chmod(
                0o600
            )

        except Exception:
            try:
                temporary_path.unlink(
                    missing_ok=True
                )
            finally:
                raise

    def _reject_symlink(self) -> None:
        if self.path.is_symlink():
            raise ValueError(
                "Signing identity path must not be a symlink"
            ) 