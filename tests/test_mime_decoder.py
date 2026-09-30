# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import pytest

from garlicsmtp.smtp.mime import MimeDecoder
from garlicsmtp.smtp.mime import (
    MimeAttachment,
    MimeDecoder,
    MimeEncoder,
)


def test_mime_decoder_decodes_quoted_printable():
    assert MimeDecoder.decode(
        "Ciao=20Giuliano!",
        "quoted-printable",
    ) == "Ciao Giuliano!"


def test_mime_decoder_removes_quoted_printable_soft_line_break():
    assert MimeDecoder.decode(
        "Prima riga molto lunga=\n"
        "che continua sulla seconda riga",
        "quoted-printable",
    ) == (
        "Prima riga molto lunga"
        "che continua sulla seconda riga"
    )


def test_mime_decoder_prefers_plain_text_in_multipart_alternative():
    body = (
        "--abc123\n"
        "Content-Type: text/plain; charset=utf-8\n"
        "\n"
        "Hello from plain text\n"
        "--abc123\n"
        "Content-Type: text/html; charset=utf-8\n"
        "\n"
        "<p>Hello from <strong>HTML</strong></p>\n"
        "--abc123--"
    )

    assert MimeDecoder.extract_multipart_alternative(
        body,
        "abc123",
    ) == "Hello from plain text"


def test_mime_decoder_extracts_multipart_mixed_attachment():
    body = (
        "--mixed123\n"
        "Content-Type: text/plain; charset=utf-8\n"
        "\n"
        "Hello from message\n"
        "--mixed123\n"
        "Content-Type: application/pdf\n"
        "Content-Disposition: attachment; filename=\"document.pdf\"\n"
        "Content-Transfer-Encoding: base64\n"
        "\n"
        "JVBERi0xLjQK\n"
        "--mixed123--"
    )

    text, attachments = (
        MimeDecoder.extract_multipart_mixed(
            body,
            "mixed123",
        )
    )

    assert text == "Hello from message"
    assert len(attachments) == 1

    attachment = attachments[0]

    assert attachment.filename == "document.pdf"
    assert attachment.declared_mime == "application/pdf"
    assert attachment.content == b"%PDF-1.4\n"


def test_mime_decoder_rejects_attachment_without_filename():
    body = (
        "--mixed123\n"
        "Content-Type: text/plain; charset=utf-8\n"
        "\n"
        "Hello from message\n"
        "--mixed123\n"
        "Content-Type: application/pdf\n"
        "Content-Disposition: attachment\n"
        "Content-Transfer-Encoding: base64\n"
        "\n"
        "JVBERi0xLjQK\n"
        "--mixed123--"
    )

    with pytest.raises(
        ValueError,
        match="Attachment has no filename",
    ):
        MimeDecoder.extract_multipart_mixed(
            body,
            "mixed123",
        )


def test_mime_encoder_round_trips_multipart_mixed_attachment():
    attachment = MimeAttachment(
        filename="document.pdf",
        declared_mime="application/pdf",
        content=b"%PDF-1.4\nattachment",
    )

    body = MimeEncoder.encode_multipart_mixed(
        text="Hello Bob",
        attachments=[
            attachment,
        ],
        boundary="mixed123",
    )

    text, attachments = (
        MimeDecoder.extract_multipart_mixed(
            body,
            "mixed123",
        )
    )

    assert text == "Hello Bob"
    assert attachments == [
        attachment,
    ]