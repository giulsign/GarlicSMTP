# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from __future__ import annotations

import re

from dataclasses import dataclass
from datetime import datetime


class IMAPAppendError(ValueError):
    pass


@dataclass(
    frozen=True,
    slots=True,
)
class IMAPAppendItem:
    flags: tuple[str, ...]
    internal_date: datetime | None
    literal_size: int
    non_synchronizing: bool


@dataclass(
    frozen=True,
    slots=True,
)
class IMAPAppendRequest:
    tag: str
    mailbox: str
    items: tuple[IMAPAppendItem, ...]

    @property
    def flags(
        self,
    ) -> frozenset[str]:
        """
        Compatibilità con l'API precedente.
        """

        return frozenset(
            self.items[0].flags
        )

    @property
    def internal_date(
        self,
    ) -> datetime | None:
        """
        Compatibilità temporanea con APPEND singolo.
        """

        return self.items[0].internal_date

    @property
    def literal_size(
        self,
    ) -> int:
        """
        Compatibilità temporanea con APPEND singolo.
        """

        return self.items[0].literal_size

    @property
    def non_synchronizing(
        self,
    ) -> bool:
        """
        Compatibilità temporanea con APPEND singolo.
        """

        return self.items[0].non_synchronizing


class _AppendCursor:
    def __init__(
        self,
        value: str,
    ) -> None:
        self.value = value
        self.position = 0

    def at_end(
        self,
    ) -> bool:
        return self.position >= len(
            self.value
        )

    def current(
        self,
    ) -> str:
        if self.at_end():
            return ""

        return self.value[
            self.position
        ]

    def skip_spaces(
        self,
    ) -> None:
        while (
            not self.at_end()
            and self.current().isspace()
        ):
            self.position += 1

    def require_space(
        self,
        message: str,
    ) -> None:
        if (
            self.at_end()
            or not self.current().isspace()
        ):
            raise IMAPAppendError(
                message
            )

        self.skip_spaces()

    def parse_atom(
        self,
    ) -> str:
        start = self.position

        while not self.at_end():
            character = self.current()

            if (
                character.isspace()
                or character
                in '(){}"'
            ):
                break

            self.position += 1

        return self.value[
            start:self.position
        ]

    def parse_quoted(
        self,
    ) -> str:
        if self.current() != '"':
            raise IMAPAppendError(
                "Expected quoted string"
            )

        self.position += 1

        result: list[str] = []

        while not self.at_end():
            character = self.current()
            self.position += 1

            if character == '"':
                return "".join(result)

            if character == "\\":
                if self.at_end():
                    raise IMAPAppendError(
                        "Unterminated quoted string"
                    )

                result.append(
                    self.current()
                )

                self.position += 1

                continue

            result.append(character)

        raise IMAPAppendError(
            "Unterminated quoted string"
        )


class IMAPAppendParser:
    _LITERAL_PATTERN = re.compile(
        r"\{([0-9]+)(\+)?\}"
    )

    _SYSTEM_FLAGS = {
        "\\seen": "\\Seen",
        "\\answered": "\\Answered",
        "\\flagged": "\\Flagged",
        "\\deleted": "\\Deleted",
        "\\draft": "\\Draft",
    }

    @classmethod
    def is_append_command(
        cls,
        line: str,
    ) -> bool:
        parts = line.strip().split(
            None,
            2,
        )

        return (
            len(parts) >= 2
            and parts[1].upper()
            == "APPEND"
        )

    @classmethod
    def parse(
        cls,
        line: str,
    ) -> IMAPAppendRequest:
        cursor = _AppendCursor(
            line.rstrip("\r\n")
        )

        cursor.skip_spaces()

        tag = cursor.parse_atom()

        if not tag:
            raise IMAPAppendError(
                "APPEND requires tag"
            )

        cursor.require_space(
            "APPEND requires command"
        )

        command = cursor.parse_atom()

        if command.upper() != "APPEND":
            raise IMAPAppendError(
                "Invalid APPEND command"
            )

        cursor.require_space(
            "APPEND requires mailbox"
        )

        mailbox = cls._parse_mailbox(
            cursor
        )

        if not mailbox:
            raise IMAPAppendError(
                "APPEND requires mailbox"
            )

        cursor.skip_spaces()

        if cursor.at_end():
            raise IMAPAppendError(
                "APPEND requires literal size"
            )

        items: list[IMAPAppendItem] = []

        while not cursor.at_end():
            items.append(
                cls._parse_item(
                    cursor
                )
            )

            cursor.skip_spaces()

        if not items:
            raise IMAPAppendError(
                "APPEND requires literal size"
            )

        return IMAPAppendRequest(
            tag=tag,
            mailbox=mailbox,
            items=tuple(items),
        )

    @classmethod
    def _parse_mailbox(
        cls,
        cursor: _AppendCursor,
    ) -> str:
        if cursor.at_end():
            raise IMAPAppendError(
                "APPEND requires mailbox"
            )

        if cursor.current() == '"':
            return cursor.parse_quoted()

        mailbox = cursor.parse_atom()

        if not mailbox:
            raise IMAPAppendError(
                "APPEND requires mailbox"
            )

        return mailbox

    @classmethod
    def _parse_item(
        cls,
        cursor: _AppendCursor,
    ) -> IMAPAppendItem:
        cursor.skip_spaces()

        flags: tuple[str, ...] = ()
        internal_date: (
            datetime | None
        ) = None

        if cursor.at_end():
            raise IMAPAppendError(
                "APPEND requires literal size"
            )

        if cursor.current() == "(":
            flags = cls._parse_flags(
                cursor
            )

            cursor.skip_spaces()

        if cursor.at_end():
            raise IMAPAppendError(
                "APPEND requires literal size"
            )

        if cursor.current() == '"':
            internal_date = (
                cls._parse_internal_date(
                    cursor
                )
            )

            cursor.skip_spaces()

        elif cursor.current() != "{":
            raise IMAPAppendError(
                "Invalid APPEND internal date"
            )

        if (
            cursor.at_end()
            or cursor.current() != "{"
        ):
            raise IMAPAppendError(
                "APPEND requires literal size"
            )

        (
            literal_size,
            non_synchronizing,
        ) = cls._parse_literal(
            cursor
        )

        return IMAPAppendItem(
            flags=flags,
            internal_date=internal_date,
            literal_size=literal_size,
            non_synchronizing=(
                non_synchronizing
            ),
        )

    @classmethod
    def _parse_flags(
        cls,
        cursor: _AppendCursor,
    ) -> tuple[str, ...]:
        if cursor.current() != "(":
            raise IMAPAppendError(
                "Invalid APPEND flag list"
            )

        cursor.position += 1

        flags: list[str] = []

        while True:
            cursor.skip_spaces()

            if cursor.at_end():
                raise IMAPAppendError(
                    "Unterminated APPEND flag list"
                )

            if cursor.current() == ")":
                cursor.position += 1
                break

            flag = cursor.parse_atom()

            if not flag:
                raise IMAPAppendError(
                    "Invalid APPEND flag list"
                )

            flags.append(
                cls._normalize_flag(
                    flag
                )
            )

        return tuple(flags)

    @classmethod
    def _normalize_flag(
        cls,
        flag: str,
    ) -> str:
        if not flag.startswith("\\"):
            return flag

        normalized = cls._SYSTEM_FLAGS.get(
            flag.lower()
        )

        if normalized is None:
            raise IMAPAppendError(
                "Unsupported system flag "
                f"{flag}"
            )

        return normalized

    @classmethod
    def _parse_internal_date(
        cls,
        cursor: _AppendCursor,
    ) -> datetime:
        value = cursor.parse_quoted()

        try:
            parsed = datetime.strptime(
                value,
                "%d-%b-%Y "
                "%H:%M:%S %z",
            )
        except ValueError as error:
            if cls._looks_like_date_without_timezone(
                value
            ):
                raise IMAPAppendError(
                    "APPEND internal date "
                    "requires timezone"
                ) from error

            raise IMAPAppendError(
                "Invalid APPEND internal date"
            ) from error

        return parsed

    @classmethod
    def _looks_like_date_without_timezone(
        cls,
        value: str,
    ) -> bool:
        try:
            datetime.strptime(
                value,
                "%d-%b-%Y "
                "%H:%M:%S",
            )
        except ValueError:
            return False

        return True

    @classmethod
    def _parse_literal(
        cls,
        cursor: _AppendCursor,
    ) -> tuple[int, bool]:
        match = cls._LITERAL_PATTERN.match(
            cursor.value,
            cursor.position,
        )

        if match is None:
            raise IMAPAppendError(
                "APPEND requires literal size"
            )

        cursor.position = match.end()

        literal_size = int(
            match.group(1)
        )

        non_synchronizing = (
            match.group(2) is not None
        )

        if (
            not cursor.at_end()
            and not cursor.current().isspace()
        ):
            raise IMAPAppendError(
                "Invalid APPEND literal size"
            )

        return (
            literal_size,
            non_synchronizing,
        )