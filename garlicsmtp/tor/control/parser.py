# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from collections.abc import Callable

from garlicsmtp.tor.control.exceptions import (
    TorControlConnectionError,
    TorControlProtocolError,
)
from garlicsmtp.tor.control.reply import (
    TorReply,
    TorReplyLine,
    TorReplySeparator,
)


ReceiveLine = Callable[
    [],
    str,
]


class TorReplyParser:

    def __init__(
        self,
        *,
        max_reply_lines: int = 10_000,
        max_data_lines: int = 100_000,
    ) -> None:
        if max_reply_lines <= 0:
            raise ValueError(
                "max_reply_lines must be "
                "greater than zero"
            )

        if max_data_lines <= 0:
            raise ValueError(
                "max_data_lines must be "
                "greater than zero"
            )

        self.max_reply_lines = (
            max_reply_lines
        )

        self.max_data_lines = (
            max_data_lines
        )

    def parse(
        self,
        receive_line: ReceiveLine,
    ) -> TorReply:
        lines: list[TorReplyLine] = []
        expected_status: int | None = None

        while True:
            raw_line = self._receive(
                receive_line
            )

            parsed_line = self._parse_header(
                raw_line
            )

            if expected_status is None:
                expected_status = (
                    parsed_line.status
                )

            elif (
                parsed_line.status
                != expected_status
            ):
                raise TorControlProtocolError(
                    "Tor Control reply contains "
                    "mismatched status codes"
                )

            if parsed_line.has_data:
                parsed_line = TorReplyLine(
                    status=parsed_line.status,
                    separator=(
                        parsed_line.separator
                    ),
                    text=parsed_line.text,
                    data=self._read_data_block(
                        receive_line
                    ),
                )

            lines.append(
                parsed_line
            )

            if (
                len(lines)
                > self.max_reply_lines
            ):
                raise TorControlProtocolError(
                    "Tor Control reply exceeds "
                    "the configured line limit"
                )

            if parsed_line.is_final:
                break

        if not lines:
            raise TorControlProtocolError(
                "Tor Control reply is empty"
            )

        return TorReply(
            status=expected_status,
            lines=tuple(
                lines
            ),
        )

    def _read_data_block(
        self,
        receive_line: ReceiveLine,
    ) -> tuple[str, ...]:
        data_lines: list[str] = []

        while True:
            line = self._receive(
                receive_line
            )

            if line == ".":
                return tuple(
                    data_lines
                )

            data_lines.append(
                self._unescape_data_line(
                    line
                )
            )

            if (
                len(data_lines)
                > self.max_data_lines
            ):
                raise TorControlProtocolError(
                    "Tor Control data block "
                    "exceeds the configured limit"
                )

    @staticmethod
    def _parse_header(
        line: str,
    ) -> TorReplyLine:
        if len(line) < 4:
            raise TorControlProtocolError(
                "Tor Control reply line "
                "is too short"
            )

        status_text = line[:3]
        separator_text = line[3]

        if not status_text.isascii():
            raise TorControlProtocolError(
                "Tor Control status code "
                "must contain ASCII digits"
            )

        if not status_text.isdigit():
            raise TorControlProtocolError(
                "Tor Control status code "
                "must contain three digits"
            )

        try:
            separator = TorReplySeparator(
                separator_text
            )
        except ValueError as exc:
            raise TorControlProtocolError(
                "Unsupported Tor Control "
                "reply separator"
            ) from exc

        return TorReplyLine(
            status=int(
                status_text
            ),
            separator=separator,
            text=line[4:],
        )

    @staticmethod
    def _unescape_data_line(
        line: str,
    ) -> str:
        if line.startswith(
            ".."
        ):
            return line[1:]

        return line

    @staticmethod
    def _receive(
        receive_line: ReceiveLine,
    ) -> str:
        try:
            line = receive_line()
        except TorControlConnectionError:
            raise
        except Exception as exc:
            raise TorControlProtocolError(
                "Unable to read Tor "
                "Control reply"
            ) from exc

        if line is None:
            raise TorControlProtocolError(
                "Tor Control reply ended "
                "unexpectedly"
            )

        if not isinstance(
            line,
            str,
        ):
            raise TorControlProtocolError(
                "Tor Control receive callback "
                "must return text lines"
            )

        return line
