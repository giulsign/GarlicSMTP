# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from dataclasses import dataclass
from enum import Enum

from garlicsmtp.imap.response import IMAPResponse


class IMAPCommandAction(Enum):
    COMPLETE = "complete"
    ENTER_IDLE = "enter_idle"


@dataclass(frozen=True)
class IMAPCommandResult:
    responses: tuple[IMAPResponse, ...]
    action: IMAPCommandAction = (
        IMAPCommandAction.COMPLETE
    )

    @classmethod
    def complete(
        cls,
        responses: list[IMAPResponse],
    ) -> "IMAPCommandResult":
        return cls(
            responses=tuple(responses),
            action=IMAPCommandAction.COMPLETE,
        )

    @classmethod
    def enter_idle(
        cls,
        responses: list[IMAPResponse],
    ) -> "IMAPCommandResult":
        return cls(
            responses=tuple(responses),
            action=IMAPCommandAction.ENTER_IDLE,
        )

    def as_list(
        self,
    ) -> list[IMAPResponse]:
        return list(self.responses)