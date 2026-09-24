# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.smtp.mime import MimeDecoder


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