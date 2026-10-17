# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import (
    ChaCha20Poly1305,
)
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


@dataclass(frozen=True)
class StoredAttachment:
    filename: str
    declared_mime: str
    content: bytes


class AttachmentStore:

    _MAGIC = b"GSAT"
    _VERSION = b"\x01"
    _NONCE_SIZE = 12

    def __init__(
        self,
        path: Path,
        *,
        dek: bytes,
    ) -> None:
        if not isinstance(dek, bytes) or len(dek) != 32:
            raise ValueError("Attachment DEK must be 32 bytes")

        self.path = path

        key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b"GarlicSMTP attachment storage v1",
        ).derive(dek)

        self._cipher = ChaCha20Poly1305(key)

    def save(
        self,
        *,
        message_id: str,
        filename: str,
        declared_mime: str,
        content: bytes,
    ) -> StoredAttachment:
        normalized_message_id = self._validate_message_id(
            message_id
        )

        message_path = self.path / normalized_message_id
        message_path.mkdir(parents=True, exist_ok=True)

        attachment_id = str(uuid4())
        target = message_path / f"{attachment_id}.gsat"

        metadata = json.dumps(
            {
                "filename": filename,
                "declared_mime": declared_mime,
                "content_length": len(content),
            },
            ensure_ascii=False,
        ).encode("utf-8")

        payload = (
            len(metadata).to_bytes(4, "big")
            + metadata
            + content
        )

        header = self._MAGIC + self._VERSION
        nonce = os.urandom(self._NONCE_SIZE)

        aad = self._aad(
            normalized_message_id,
            attachment_id,
            header,
        )

        ciphertext = self._cipher.encrypt(
            nonce,
            payload,
            aad,
        )

        encrypted = header + nonce + ciphertext

        temporary = message_path / f".{attachment_id}.tmp"

        try:
            with temporary.open("xb") as file:
                file.write(encrypted)

            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)

        return StoredAttachment(
            filename=filename,
            declared_mime=declared_mime,
            content=content,
        )

    def delete_for_message(
        self,
        message_id: str,
    ) -> None:
        normalized_message_id = (
            self._validate_message_id(
                message_id
            )
        )

        shutil.rmtree(
            self.path
            / normalized_message_id,
            ignore_errors=True,
        )

    @staticmethod
    def _validate_message_id(
        message_id: str,
    ) -> str:
        if not isinstance(
            message_id,
            str,
        ):
            raise TypeError(
                "message id must be text"
            )

        normalized = message_id.strip()

        if not normalized:
            raise ValueError(
                "message id cannot be empty"
            )

        if (
            "/" in normalized
            or "\\" in normalized
            or Path(normalized).is_absolute()
            or normalized in {
                ".",
                "..",
            }
        ):
            raise ValueError(
                "message id is not safe"
            )

        return normalized

    def list_for_message(
        self,
        message_id: str,
    ) -> list[StoredAttachment]:
        normalized_message_id = self._validate_message_id(
            message_id
        )

        message_path = self.path / normalized_message_id

        if not message_path.is_dir():
            return []

        legacy_files = [
            path
            for path in message_path.iterdir()
            if path.is_file()
            and path.suffix in {".bin", ".json"}
        ]

        if legacy_files:
            raise ValueError(
                "legacy plaintext attachments require migration"
            )

        attachments = []

        for encrypted_path in sorted(
            message_path.glob("*.gsat")
        ):
            encrypted = encrypted_path.read_bytes()

            header_size = len(self._MAGIC) + len(self._VERSION)
            minimum_size = header_size + self._NONCE_SIZE + 16

            if len(encrypted) < minimum_size:
                raise ValueError("Invalid encrypted attachment")

            header = encrypted[:header_size]

            if header != self._MAGIC + self._VERSION:
                raise ValueError(
                    "Unsupported encrypted attachment format"
                )

            nonce = encrypted[
                header_size : header_size + self._NONCE_SIZE
            ]
            ciphertext = encrypted[
                header_size + self._NONCE_SIZE :
            ]

            aad = self._aad(
                normalized_message_id,
                encrypted_path.stem,
                header,
            )

            payload = self._cipher.decrypt(
                nonce,
                ciphertext,
                aad,
            )

            if len(payload) < 4:
                raise ValueError("Invalid attachment payload")

            metadata_length = int.from_bytes(
                payload[:4],
                "big",
            )

            metadata_end = 4 + metadata_length

            if metadata_end > len(payload):
                raise ValueError("Invalid attachment metadata")

            metadata = json.loads(
                payload[4:metadata_end].decode("utf-8")
            )
            content = payload[metadata_end:]

            if len(content) != metadata["content_length"]:
                raise ValueError("Invalid attachment content length")

            attachments.append(
                StoredAttachment(
                    filename=metadata["filename"],
                    declared_mime=metadata["declared_mime"],
                    content=content,
                )
            )

        return attachments

    @staticmethod
    def _aad(
        message_id: str,
        attachment_id: str,
        header: bytes,
    ) -> bytes:
        message_bytes = message_id.encode("utf-8")
        attachment_bytes = attachment_id.encode("utf-8")

        return (
            header
            + len(message_bytes).to_bytes(4, "big")
            + message_bytes
            + len(attachment_bytes).to_bytes(4, "big")
            + attachment_bytes
        )

    def directory_for_message(
        self,
        message_id: str,
    ) -> Path:
        normalized_message_id = (
            self._validate_message_id(
                message_id
            )
        )

        return (
            self.path
            / normalized_message_id
        )

    def materialize_for_message(
        self,
        message_id: str,
        destination: Path,
    ) -> Path:
        attachments = self.list_for_message(
            message_id
        )

        filenames = set()

        for attachment in attachments:
            filename = attachment.filename

            if (
                not isinstance(filename, str)
                or not filename
                or Path(filename).name != filename
                or "/" in filename
                or "\\" in filename
                or Path(filename).is_absolute()
                or filename in {
                    ".",
                    "..",
                }
            ):
                raise ValueError(
                    "attachment filename is not safe"
                )

            if filename in filenames:
                raise ValueError(
                    "duplicate attachment filename"
                )

            filenames.add(filename)

        destination.mkdir(
            parents=True,
            exist_ok=True,
        )

        for attachment in attachments:
            (
                destination
                / attachment.filename
            ).write_bytes(
                attachment.content
            )

        return destination
        