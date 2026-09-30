# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from dataclasses import dataclass
import shutil
from pathlib import Path
from uuid import uuid4
import json


@dataclass(frozen=True)
class StoredAttachment:
    filename: str
    declared_mime: str
    content: bytes


class AttachmentStore:

    def __init__(
        self,
        path: Path,
    ) -> None:
        self.path = path

    def save(
        self,
        *,
        message_id: str,
        filename: str,
        declared_mime: str,
        content: bytes,
    ) -> StoredAttachment:
        normalized_message_id = (
            self._validate_message_id(
                message_id
            )   
        )

        message_path = (
            self.path
            / normalized_message_id
        )

        message_path.mkdir(
            parents=True,
            exist_ok=True,
        )

        attachment_id = str(
            uuid4()
        )

        content_path = (
            message_path
            / f"{attachment_id}.bin"
        )

        metadata_path = (
            message_path
            / f"{attachment_id}.json"
        )

        content_path.write_bytes(
            content
        )

        metadata_path.write_text(
            json.dumps(
                {
                    "filename": filename,
                    "declared_mime": (
                        declared_mime
                    ),
                }
            ),
            encoding="utf-8",
        )

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
        normalized_message_id = (
            self._validate_message_id(
                message_id
            )
        )

        message_path = (
            self.path
            / normalized_message_id
        )

        if not message_path.is_dir():
            return []

        attachments = []

        for metadata_path in sorted(
            message_path.glob("*.json")
        ):
            attachment_id = (
                metadata_path.stem
            )

            content_path = (
                message_path
                / f"{attachment_id}.bin"
            )

            metadata = json.loads(
                metadata_path.read_text(
                    encoding="utf-8"
                )
            )

            attachments.append(
                StoredAttachment(
                    filename=(
                        metadata["filename"]
                    ),
                    declared_mime=(
                        metadata[
                            "declared_mime"
                        ]
                    ),
                    content=(
                        content_path.read_bytes()
                    ),
                )
            )

        return attachments

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
        