# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from dataclasses import dataclass


@dataclass(
    frozen=True,
    slots=True,
)
class MailboxSummary:

    address: str
    message_count: int

    def __post_init__(
        self,
    ) -> None:
        if not self.address:
            raise ValueError(
                "mailbox address cannot be empty"
            )

        if self.message_count < 0:
            raise ValueError(
                "message_count cannot be negative"
            )
