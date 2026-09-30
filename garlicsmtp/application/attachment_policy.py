# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from pathlib import Path


class AttachmentTypeRejected(
    ValueError
):
    pass


_ALLOWED_TYPES = {
    ".jpg": (
        "image/jpeg",
        b"\xff\xd8\xff",
    ),
    ".jpeg": (
        "image/jpeg",
        b"\xff\xd8\xff",
    ),
    ".png": (
        "image/png",
        b"\x89PNG\r\n\x1a\n",
    ),
    ".pdf": (
        "application/pdf",
        b"%PDF-",
    ),
}


def validate_attachment_type(
    *,
    filename: str,
    declared_mime: str,
    content: bytes,
) -> None:
    extension = Path(
        filename
    ).suffix.lower()

    if extension == ".txt":
        if declared_mime != "text/plain":
            raise AttachmentTypeRejected(
                "attachment MIME type does not match extension"
            )

        if b"\x00" in content:
            raise AttachmentTypeRejected(
                "plain text attachment contains NUL bytes"
            )

        try:
            content.decode(
                "utf-8"
            )
        except UnicodeDecodeError as exc:
            raise AttachmentTypeRejected(
                "plain text attachment is not valid UTF-8"
            ) from exc

        return

    
    expected = _ALLOWED_TYPES.get(
        extension
    )

    if expected is None:
        raise AttachmentTypeRejected(
            "attachment type is not allowed"
        )

    expected_mime, magic_bytes = expected

    if declared_mime != expected_mime:
        raise AttachmentTypeRejected(
            "attachment MIME type does not match extension"
        )

    if not content.startswith(
        magic_bytes
    ):
        raise AttachmentTypeRejected(
            "attachment content does not match declared type"
        )
