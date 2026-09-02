# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import base64
import json
import quopri
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
    def to_rfc5322(message):
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

        body = message.body or ""

        content_type = message.headers.get(
            "Content-Type",
            "",
        )

        encoding = message.headers.get(
            "Content-Transfer-Encoding",
            "",
        )

        if content_type.lower().startswith(
            "multipart/alternative"
        ):
            boundary = ""

            for parameter in content_type.split(";")[1:]:
                name, separator, value = (
                    parameter.partition("=")
                )

                if (
                    separator
                    and name.strip().lower()
                    == "boundary"
                ):
                    boundary = (
                        value.strip()
                        .strip('"')
                    )
                    break

            if boundary:
                body = "\r\n".join(
                    [
                        f"--{boundary}",
                        "Content-Type: text/plain; charset=utf-8",
                        "",
                        body,
                        f"--{boundary}--",
                    ]
                )

        elif encoding.lower() == "quoted-printable":
            body = quopri.encodestring(
                body.encode("utf-8")
            ).decode("ascii")

        elif encoding.lower() == "base64":
            body = base64.b64encode(
                body.encode("utf-8")
            ).decode("ascii")

        lines.append(body)

        return "\r\n".join(lines)