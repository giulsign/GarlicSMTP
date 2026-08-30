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
