# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import base64
import json
from pathlib import Path
import os
import tempfile

class MemoryEncryptionKeyStore:

    def __init__(self):
        self._keys: dict[str, bytes] = {}

    def remember(
        self,
        hostname: str,
        public_key: bytes,
    ) -> None:
        existing = self._keys.get(
            hostname
        )

        if (
            existing is not None
            and existing != public_key
        ):
            raise ValueError(
                "encryption key changed"
            )

        self._keys[hostname] = public_key

    def get(
        self,
        hostname: str,
    ) -> bytes | None:
        return self._keys.get(
            hostname
        )

class FileEncryptionKeyStore:

    def __init__(
        self,
        path: Path,
    ):  
        self.path = Path(path)
        self._reject_symlink()
        self._keys = self._load()
        self._reject_symlink()

    def remember(
        self,
        hostname: str,
        public_key: bytes,
    ) -> None:
        existing = self._keys.get(
            hostname
        )

        if (
            existing is not None
            and existing != public_key
        ):
            raise ValueError(
                "encryption key changed"
            )

        self._keys[hostname] = public_key
        self._save()

    def get(
        self,
        hostname: str,
    ) -> bytes | None:
        return self._keys.get(
            hostname
        )

    def _load(
        self,
    ) -> dict[str, bytes]:
        if not self.path.exists():
            return {}

        data = json.loads(
            self.path.read_text(
                encoding="utf-8",
            )
        )

        return {
            hostname: base64.b64decode(
                encoded_key,
                validate=True,
            )
            for hostname, encoded_key
            in data.items()
        }

    def _save(
        self,
    ) -> None:

        self._reject_symlink()

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.path.parent.chmod(
            0o700
        )

        data = {
            hostname: base64.b64encode(
                public_key
            ).decode("ascii")
            for hostname, public_key
            in self._keys.items()
        }

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
                "w",
                encoding="utf-8",
            ) as handle:
                handle.write(
                    json.dumps(
                        data,
                        sort_keys=True,
                        separators=(",", ":"),
                    )
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

    def _reject_symlink(
        self,
    ) -> None:
        if self.path.is_symlink():
            raise ValueError(
                "Encryption key store path "
                "must not be a symlink"
            )