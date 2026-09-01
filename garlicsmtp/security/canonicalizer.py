# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import json

from garlicsmtp.models import MailMessage
from garlicsmtp.security.signature_header import (
    SIGNATURE_HEADER,
)

class MessageCanonicalizer:

    VERSION = 1

    @classmethod
    def canonicalize(
        cls,
        message: MailMessage,
    ) -> bytes:
        data = {
            "version": cls.VERSION,
            "envelope": {
                "sender": message.envelope.sender,
                "recipients": list(
                    message.envelope.recipients
                ),
            },
            "headers": {
                name.lower(): value
                for name, value in message.headers.fields.items()
                if name.lower() != SIGNATURE_HEADER.lower()
            },
            "body": message.body or "",
        }

        text = json.dumps(
            data,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

        return text.encode("utf-8")


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