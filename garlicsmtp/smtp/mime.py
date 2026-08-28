# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from quopri import decodestring
from email import policy
from email.parser import Parser


class MimeDecoder:

    @staticmethod
    def decode(
        body: str,
        encoding: str,
    ) -> str:

        normalized = encoding.strip().lower()

        if normalized == "quoted-printable":
            return decodestring(
                body.encode("utf-8")
            ).decode(
                "utf-8"
            )

        return body

    @staticmethod
    def extract_multipart_alternative(
        body: str,
        boundary: str,
    ) -> str:

        message = Parser(
            policy=policy.default
        ).parsestr(
            (
                "Content-Type: multipart/alternative; "
                f'boundary="{boundary}"\n'
                "\n"
                f"{body}"
            )
        )

        for part in message.iter_parts():
            if part.get_content_type() != "text/plain":
                continue

            content = part.get_content()

            if isinstance(
                content,
                str,
            ):
                return content.strip()

        return body
