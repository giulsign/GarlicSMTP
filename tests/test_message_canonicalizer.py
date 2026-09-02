# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.models import (
    Envelope,
    MailHeaders,
    MailMessage,
)
from garlicsmtp.security.canonicalizer import (
    MessageCanonicalizer,
)
from garlicsmtp.security.signature_header import (
    SIGNATURE_HEADER,
)


def test_canonicalizer_is_deterministic():
    first = MailMessage(
        envelope=Envelope(
            sender="alice@test.onion",
            recipients=[
                "bob@test.onion",
            ],
        ),
        headers=MailHeaders(
            fields={
                "Subject": "Hello",
                "Content-Type": "text/plain",
            }
        ),
        body="Hello Bob",
    )

    second = MailMessage(
        envelope=Envelope(
            sender="alice@test.onion",
            recipients=[
                "bob@test.onion",
            ],
        ),
        headers=MailHeaders(
            fields={
                "Content-Type": "text/plain",
                "Subject": "Hello",
            }
        ),
        body="Hello Bob",
    )

    assert (
        MessageCanonicalizer.canonicalize(first)
        == MessageCanonicalizer.canonicalize(second)
    )


def build_message():
    return MailMessage(
        envelope=Envelope(
            sender="alice@test.onion",
            recipients=[
                "bob@test.onion",
            ],
        ),
        headers=MailHeaders(
            fields={
                "Subject": "Hello",
                "Content-Type": "text/plain",
            }
        ),
        body="Hello Bob",
    )


def test_canonicalizer_changes_when_sender_changes():
    first = build_message()
    second = build_message()

    second.envelope.sender = "mallory@test.onion"

    assert (
        MessageCanonicalizer.canonicalize(first)
        != MessageCanonicalizer.canonicalize(second)
    )


def test_canonicalizer_changes_when_recipients_change():
    first = build_message()
    second = build_message()

    second.envelope.recipients = [
        "carol@test.onion",
    ]

    assert (
        MessageCanonicalizer.canonicalize(first)
        != MessageCanonicalizer.canonicalize(second)
    )


def test_canonicalizer_changes_when_header_changes():
    first = build_message()
    second = build_message()

    second.headers.fields["Subject"] = "Changed"

    assert (
        MessageCanonicalizer.canonicalize(first)
        != MessageCanonicalizer.canonicalize(second)
    )


def test_canonicalizer_changes_when_body_changes():
    first = build_message()
    second = build_message()

    second.body = "Modified body"

    assert (
        MessageCanonicalizer.canonicalize(first)
        != MessageCanonicalizer.canonicalize(second)
    )


def test_canonicalizer_returns_utf8_bytes():
    message = build_message()
    message.body = "Caffè ☕"

    canonical = MessageCanonicalizer.canonicalize(
        message
    )

    assert isinstance(canonical, bytes)
    assert "Caffè ☕" in canonical.decode("utf-8")


def test_canonicalizer_excludes_signature_header():
    first = build_message()
    second = build_message()

    first.headers.fields[
        SIGNATURE_HEADER
    ] = (
        "v=1; alg=ed25519; "
        "key=abc; sig=first"
    )

    second.headers.fields[
        SIGNATURE_HEADER
    ] = (
        "v=1; alg=ed25519; "
        "key=abc; sig=second"
    )

    assert (
        MessageCanonicalizer.canonicalize(first)
        == MessageCanonicalizer.canonicalize(second)
    )


def test_canonicalizer_normalizes_header_names_case_insensitively():
    first = MailMessage(
        envelope=Envelope(
            sender="alice@sender.onion",
            recipients=[
                "bob@receiver.onion",
            ],
        ),
        headers=MailHeaders(
            fields={
                "Subject": "Hello",
            }
        ),
        body="Hello",
    )

    second = MailMessage(
        envelope=Envelope(
            sender="alice@sender.onion",
            recipients=[
                "bob@receiver.onion",
            ],
        ),
        headers=MailHeaders(
            fields={
                "subject": "Hello",
            }
        ),
        body="Hello",
    )

    assert (
        MessageCanonicalizer.canonicalize(first)
        == MessageCanonicalizer.canonicalize(second)
    )


def test_canonicalizer_excludes_signature_header_case_insensitively():
    first = build_message()
    second = build_message()

    first.headers.fields[
        "X-GarlicSMTP-Signature"
    ] = "v=1; alg=ed25519; key=abc; sig=first"

    second.headers.fields[
        "x-garlicsmtp-signature"
    ] = "v=1; alg=ed25519; key=abc; sig=second"

    assert (
        MessageCanonicalizer.canonicalize(first)
        == MessageCanonicalizer.canonicalize(second)
    )


def test_canonicalizer_distinguishes_unicode_normalization_forms():
    first = build_message()
    second = build_message()

    first.body = "Café"
    second.body = "Cafe\u0301"

    assert first.body != second.body

    assert (
        MessageCanonicalizer.canonicalize(first)
        != MessageCanonicalizer.canonicalize(second)
    )


def test_canonicalizer_changes_when_recipient_order_changes():
    first = build_message()
    second = build_message()

    first.envelope.recipients = [
        "bob@test.onion",
        "carol@test.onion",
    ]

    second.envelope.recipients = [
        "carol@test.onion",
        "bob@test.onion",
    ]

    assert (
        MessageCanonicalizer.canonicalize(first)
        != MessageCanonicalizer.canonicalize(second)
    )