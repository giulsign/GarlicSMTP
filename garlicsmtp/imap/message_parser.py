# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from __future__ import annotations

from email import policy
from email.parser import BytesParser
from email.utils import getaddresses, parseaddr

from garlicsmtp.models import (
    Envelope,
    MailHeaders,
    MailMessage,
    Metadata,
)


class IMAPMessageParseError(ValueError):
    """Raised when an APPEND literal is not a valid message."""


class IMAPMessageParser:
    @classmethod
    def parse(
        cls,
        literal: bytes,
    ) -> MailMessage:
        if not literal:
            raise IMAPMessageParseError(
                "APPEND literal is empty"
            )

        try:
            parsed = BytesParser(
                policy=policy.default
            ).parsebytes(
                literal
            )
        except Exception as exc:
            raise IMAPMessageParseError(
                "Invalid RFC5322 message"
            ) from exc

        sender = cls._parse_sender(
            parsed.get(
                "From",
                "",
            )
        )

        recipients = cls._parse_recipients(
            parsed.get_all(
                "To",
                [],
            )
            + parsed.get_all(
                "Cc",
                [],
            )
            + parsed.get_all(
                "Bcc",
                [],
            )
        )

        headers = MailHeaders(
            fields={
                name: value
                for name, value
                in parsed.items()
            }
        )

        return MailMessage(
            envelope=Envelope(
                sender=sender,
                recipients=recipients,
            ),
            headers=headers,
            metadata=Metadata(),
            body=cls._extract_body(
                parsed
            ),
        )

    @staticmethod
    def _parse_sender(
        value: str,
    ) -> str:
        _, address = parseaddr(
            value
        )

        return address

    @staticmethod
    def _parse_recipients(
        values: list[str],
    ) -> list[str]:
        return [
            address
            for _, address
            in getaddresses(values)
            if address
        ]

    @classmethod
    def _extract_body(
        cls,
        parsed,
    ) -> str:
        if parsed.is_multipart():
            plain_part = parsed.get_body(
                preferencelist=(
                    "plain",
                    "html",
                )
            )

            if plain_part is None:
                return ""

            return cls._part_content(
                plain_part
            )

        return cls._part_content(
            parsed
        )

    @staticmethod
    def _part_content(
        part,
    ) -> str:
        try:
            content = part.get_content()
        except (
            LookupError,
            UnicodeDecodeError,
        ) as exc:
            raise IMAPMessageParseError(
                "Invalid message body encoding"
            ) from exc

        if isinstance(content, bytes):
            return content.decode(
                "utf-8",
                errors="replace",
            )

        return str(content)