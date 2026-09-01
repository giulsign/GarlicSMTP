# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.models import MailHeaders


def test_mail_headers_get_is_case_insensitive():
    headers = MailHeaders()

    headers.add(
        "Content-Type",
        "text/plain",
    )

    assert (
        headers.get("content-type")
        == "text/plain"
    )

    assert (
        headers.get("CONTENT-TYPE")
        == "text/plain"
    )


def test_mail_headers_get_case_insensitive_preserves_default():
    headers = MailHeaders()

    assert (
        headers.get(
            "missing-header",
            "fallback",
        )
        == "fallback"
    )


def test_mail_headers_add_replaces_case_insensitively():
    headers = MailHeaders()

    headers.add(
        "Subject",
        "first",
    )

    headers.add(
        "subject",
        "second",
    )

    assert len(headers.fields) == 1

    assert (
        headers.get("Subject")
        == "second"
    )
