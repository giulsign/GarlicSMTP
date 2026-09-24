# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from garlicsmtp.tor.control.exceptions import (
    TorControlProtocolError,
)
from garlicsmtp.tor.control.reply import (
    TorReply,
)


class TorAuthenticationMethod(Enum):

    NULL = "NULL"
    HASHEDPASSWORD = "HASHEDPASSWORD"
    COOKIE = "COOKIE"
    SAFECOOKIE = "SAFECOOKIE"

    @classmethod
    def from_text(
        cls,
        value: str,
    ) -> "TorAuthenticationMethod | None":
        normalized = value.strip().upper()

        try:
            return cls(
                normalized
            )
        except ValueError:
            return None


@dataclass(
    frozen=True,
    slots=True,
)
class ProtocolInfo:

    protocol_version: int
    tor_version: str | None

    authentication_methods: frozenset[
        TorAuthenticationMethod
    ]

    cookie_file: Path | None

    @property
    def supports_safecookie(
        self,
    ) -> bool:
        return (
            TorAuthenticationMethod.SAFECOOKIE
            in self.authentication_methods
        )

    @property
    def supports_deprecated_cookie(
        self,
    ) -> bool:
        return (
            TorAuthenticationMethod.COOKIE
            in self.authentication_methods
        )


class ProtocolInfoParser:

    def parse(
        self,
        reply: TorReply,
    ) -> ProtocolInfo:
        if not reply.successful:
            raise TorControlProtocolError(
                "PROTOCOLINFO command failed "
                f"with status {reply.status}"
            )

        protocol_version = None
        tor_version = None
        authentication_methods = frozenset()
        cookie_file = None

        for line in reply.lines:
            keyword = line.keyword

            if keyword is None:
                continue

            normalized = keyword.upper()

            if normalized == "PROTOCOLINFO":
                protocol_version = (
                    self._parse_protocol_version(
                        line.text
                    )
                )

            elif normalized == "AUTH":
                (
                    authentication_methods,
                    cookie_file,
                ) = self._parse_auth_line(
                    line.text
                )

            elif normalized == "VERSION":
                tor_version = (
                    self._parse_version_line(
                        line.text
                    )
                )

        if protocol_version is None:
            raise TorControlProtocolError(
                "PROTOCOLINFO reply does not "
                "contain a protocol version"
            )

        return ProtocolInfo(
            protocol_version=protocol_version,
            tor_version=tor_version,
            authentication_methods=(
                authentication_methods
            ),
            cookie_file=cookie_file,
        )

    @staticmethod
    def _parse_protocol_version(
        text: str,
    ) -> int:
        parts = text.split()

        if len(parts) < 2:
            raise TorControlProtocolError(
                "Malformed PROTOCOLINFO line"
            )

        version_text = parts[1]

        if not version_text.isdigit():
            raise TorControlProtocolError(
                "PROTOCOLINFO version must "
                "be numeric"
            )

        return int(
            version_text
        )

    def _parse_auth_line(
        self,
        text: str,
    ) -> tuple[
        frozenset[TorAuthenticationMethod],
        Path | None,
    ]:
        arguments = self._parse_arguments(
            text,
            expected_keyword="AUTH",
        )

        methods_text = arguments.get(
            "METHODS"
        )

        if methods_text is None:
            raise TorControlProtocolError(
                "AUTH line does not contain "
                "METHODS"
            )

        methods = frozenset(
            method
            for method_name in methods_text.split(
                ","
            )
            if (
                method := (
                    TorAuthenticationMethod
                    .from_text(
                        method_name
                    )
                )
            )
            is not None
        )

        cookie_file_text = arguments.get(
            "COOKIEFILE"
        )

        cookie_file = (
            Path(
                cookie_file_text
            )
            if cookie_file_text
            else None
        )

        return (
            methods,
            cookie_file,
        )

    def _parse_version_line(
        self,
        text: str,
    ) -> str | None:
        arguments = self._parse_arguments(
            text,
            expected_keyword="VERSION",
        )

        return arguments.get(
            "TOR"
        )

    def _parse_arguments(
        self,
        text: str,
        *,
        expected_keyword: str,
    ) -> dict[str, str]:
        keyword, separator, remainder = (
            text.partition(
                " "
            )
        )

        if (
            keyword.upper()
            != expected_keyword.upper()
        ):
            raise TorControlProtocolError(
                "Unexpected Tor Control "
                "reply keyword"
            )

        if not separator:
            return {}

        return self._tokenize_arguments(
            remainder
        )

    def _tokenize_arguments(
        self,
        text: str,
    ) -> dict[str, str]:
        arguments: dict[str, str] = {}
        position = 0
        length = len(text)

        while position < length:
            while (
                position < length
                and text[position].isspace()
            ):
                position += 1

            if position >= length:
                break

            key_start = position

            while (
                position < length
                and not text[position].isspace()
                and text[position] != "="
            ):
                position += 1

            key = text[
                key_start:position
            ]

            if not key:
                raise TorControlProtocolError(
                    "Malformed Tor Control "
                    "argument name"
                )

            if (
                position >= length
                or text[position] != "="
            ):
                while (
                    position < length
                    and not text[position].isspace()
                ):
                    position += 1

                continue

            position += 1

            if (
                position < length
                and text[position] == '"'
            ):
                value, position = (
                    self._parse_quoted_string(
                        text,
                        position,
                    )
                )

            else:
                value_start = position

                while (
                    position < length
                    and not text[position].isspace()
                ):
                    position += 1

                value = text[
                    value_start:position
                ]

            arguments[
                key.upper()
            ] = value

        return arguments

    def _parse_quoted_string(
        self,
        text: str,
        position: int,
    ) -> tuple[str, int]:
        if text[position] != '"':
            raise TorControlProtocolError(
                "Quoted string must begin "
                "with a quote"
            )

        position += 1
        result: list[str] = []

        while position < len(text):
            character = text[position]

            if character == '"':
                return (
                    "".join(
                        result
                    ),
                    position + 1,
                )

            if character != "\\":
                result.append(
                    character
                )
                position += 1
                continue

            position += 1

            if position >= len(text):
                raise TorControlProtocolError(
                    "Unterminated escape sequence "
                    "in quoted string"
                )

            escaped = text[position]

            if escaped == "n":
                result.append(
                    "\n"
                )
                position += 1
                continue

            if escaped == "r":
                result.append(
                    "\r"
                )
                position += 1
                continue

            if escaped == "t":
                result.append(
                    "\t"
                )
                position += 1
                continue

            if escaped in "01234567":
                octal_digits = escaped
                position += 1

                while (
                    position < len(text)
                    and len(octal_digits) < 3
                    and text[position] in "01234567"
                ):
                    octal_digits += text[
                        position
                    ]
                    position += 1

                result.append(
                    chr(
                        int(
                            octal_digits,
                            8,
                        )
                    )
                )

                continue

            result.append(
                escaped
            )
            position += 1

        raise TorControlProtocolError(
            "Unterminated quoted string"
        )
