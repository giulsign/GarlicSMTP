# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import pytest

from garlicsmtp.application.attachment_policy import (
    AttachmentTypeRejected,
    validate_attachment_type,
)


@pytest.mark.parametrize(
    (
        "filename",
        "declared_mime",
        "content",
    ),
    [
        (
            "photo.jpg",
            "image/jpeg",
            b"\xff\xd8\xff\xe0",
        ),
        (
            "photo.jpeg",
            "image/jpeg",
            b"\xff\xd8\xff\xe0",
        ),
        (
            "image.png",
            "image/png",
            b"\x89PNG\r\n\x1a\n",
        ),
        (
            "document.pdf",
            "application/pdf",
            b"%PDF-1.7\n",
        ),
    ],
)
def test_attachment_policy_accepts_matching_types(
    filename,
    declared_mime,
    content,
):
    validate_attachment_type(
        filename=filename,
        declared_mime=declared_mime,
        content=content,
    )


@pytest.mark.parametrize(
    (
        "filename",
        "declared_mime",
        "content",
    ),
    [
        (
            "payload.jpg",
            "image/jpeg",
            b"MZ\x90\x00",
        ),
        (
            "payload.png",
            "image/png",
            b"MZ\x90\x00",
        ),
        (
            "payload.pdf",
            "application/pdf",
            b"MZ\x90\x00",
        ),
        (
            "photo.jpg",
            "image/png",
            b"\xff\xd8\xff\xe0",
        ),
        (
            "image.png",
            "image/jpeg",
            b"\x89PNG\r\n\x1a\n",
        ),
        (
            "document.pdf",
            "image/jpeg",
            b"%PDF-1.7\n",
        ),
        (
            "payload.exe",
            "application/octet-stream",
            b"MZ\x90\x00",
        ),
    ],
)
def test_attachment_policy_rejects_mismatched_or_disallowed_types(
    filename,
    declared_mime,
    content,
):
    with pytest.raises(
        AttachmentTypeRejected
    ):
        validate_attachment_type(
            filename=filename,
            declared_mime=declared_mime,
            content=content,
        )


def test_attachment_policy_accepts_utf8_plain_text():
    validate_attachment_type(
        filename="message.txt",
        declared_mime="text/plain",
        content=(
            "Messaggio GarlicSMTP."
            .encode("utf-8")
        ),
    )


@pytest.mark.parametrize(
    (
        "filename",
        "declared_mime",
        "content",
    ),
    [
        (
            "message.txt",
            "application/octet-stream",
            b"plain text",
        ),
        (
            "message.txt",
            "text/plain",
            b"text\x00binary",
        ),
        (
            "message.txt",
            "text/plain",
            b"\xff\xfe\xfa",
        ),
    ],
)
def test_attachment_policy_rejects_invalid_plain_text(
    filename,
    declared_mime,
    content,
):
    with pytest.raises(
        AttachmentTypeRejected
    ):
        validate_attachment_type(
            filename=filename,
            declared_mime=declared_mime,
            content=content,
        )

