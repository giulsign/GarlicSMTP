# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from abc import ABC, abstractmethod
import base64
import json
from pathlib import Path
import os
import tempfile

class TrustStore(ABC):

    @abstractmethod
    def trust(
        self,
        sender: str,
        public_key: bytes,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def is_trusted(
        self,
        sender: str,
        public_key: bytes,
    ) -> bool:
        raise NotImplementedError


class MemoryTrustStore(TrustStore):

    def __init__(self):
        self._trusted: dict[str, bytes] = {}

    def trust(
        self,
        sender: str,
        public_key: bytes,
    ) -> None:
        self._trusted[sender] = public_key

    def is_trusted(
        self,
        sender: str,
        public_key: bytes,
    ) -> bool:
        return (
            self._trusted.get(sender)
            == public_key
        )

class FileTrustStore(TrustStore):

    def __init__(
        self,
        path: Path,
    ):
        self.path = Path(path)
        self._reject_symlink()
        self._trusted = self._load()

    def trust(
        self,
        sender: str,
        public_key: bytes,
    ) -> None:
        self._trusted[sender] = public_key
        self._save()

    def is_trusted(
        self,
        sender: str,
        public_key: bytes,
    ) -> bool:
        return (
            self._trusted.get(sender)
            == public_key
        )

    def _load(self) -> dict[str, bytes]:
        if not self.path.exists():
            return {}

        data = json.loads(
            self.path.read_text(
                encoding="utf-8"
            )
        )

        return {
            sender: base64.b64decode(
                encoded_key,
                validate=True,
            )
            for sender, encoded_key in data.items()
        }

    def _save(self) -> None:
        self._reject_symlink()

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.path.parent.chmod(
            0o700
        )

        data = {
            sender: base64.b64encode(
                public_key
            ).decode("ascii")
            for sender, public_key in self._trusted.items()
        }

        serialized = json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":"),
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
                "w",
                encoding="utf-8",
            ) as handle:
                handle.write(
                    serialized
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
                "Trust store path must not be a symlink"
            )