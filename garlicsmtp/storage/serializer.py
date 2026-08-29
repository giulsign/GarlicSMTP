# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import json
from dataclasses import asdict 

from garlicsmtp.models import (
    Envelope,
    MailHeaders,
    MailMessage,
)


class MessageSerializer:

    @staticmethod
    def to_dict(
        message: MailMessage,
    ) -> dict:
        data = asdict(message)

        return data

    @staticmethod
    def to_json(
        message: MailMessage,
    ) -> str:
        return json.dumps(
            MessageSerializer.to_dict(message),
            indent=4,
            ensure_ascii=False,
        )

    @staticmethod
    def from_dict(
        data: dict,
    ) -> MailMessage:
        
        return MailMessage(
            envelope=Envelope(
                **data["envelope"]
            ),
            headers=MailHeaders(
                **data["headers"]
            ),
            body=data["body"],
        )

    @staticmethod
    def from_json(
        text: str,
    ) -> MailMessage:
        return MessageSerializer.from_dict(
            json.loads(text)
        )

    @staticmethod
    def to_rfc5322(
        message: MailMessage,
    ) -> str:
        lines = []

        for name, value in message.headers.fields.items():
            if isinstance(value, list):
                for item in value:
                    lines.append(
                        f"{name}: {item}"
                    )
            else:
                lines.append(
                    f"{name}: {value}"
                )

        lines.append("")
        lines.append(message.body or "")

        return "\r\n".join(lines)