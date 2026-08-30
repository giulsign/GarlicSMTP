# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import json

from garlicsmtp.models import MailMessage


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
            "headers": dict(
                message.headers.fields
            ),
            "body": message.body or "",
        }

        text = json.dumps(
            data,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

        return text.encode("utf-8")
