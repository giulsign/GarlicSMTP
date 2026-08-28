# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import shlex
from dataclasses import dataclass


class IMAPParseError(ValueError):
    pass


@dataclass(slots=True)
class IMAPCommand:

    tag: str

    name: str

    arguments: list[str]


class IMAPParser:

    @staticmethod
    def parse(
        line: str,
    ) -> IMAPCommand:
        text = line.strip()

        if not text:
            raise IMAPParseError(
                "Empty IMAP command"
            )

        try:
            lexer = shlex.shlex(
                text,
                posix=True,
            )

            lexer.whitespace_split = True
            lexer.commenters = ""

            # In IMAP il backslash fa parte dei flag di sistema,
            # per esempio \Seen e \Flagged. Non deve essere
            # interpretato come escape da shlex.
            lexer.escape = ""

            parts = list(lexer)

        except ValueError as exc:
            raise IMAPParseError(
                f"Invalid IMAP command: {exc}"
            ) from exc

        if len(parts) < 2:
            raise IMAPParseError(
                "IMAP command requires tag and name"
            )

        tag = parts[0]
        name = parts[1].upper()
        arguments = parts[2:]

        if tag == "*":
            raise IMAPParseError(
                "Invalid IMAP command tag"
            )

        return IMAPCommand(
            tag=tag,
            name=name,
            arguments=arguments,
        )