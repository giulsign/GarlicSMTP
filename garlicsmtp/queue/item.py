# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from dataclasses import dataclass
from datetime import UTC, datetime

from garlicsmtp.models import MailMessage


@dataclass(slots=True)
class QueueItem:

    id: str

    created: datetime

    attempts: int = 0

    next_retry: datetime | None = None

    last_error: str | None = None

    message: MailMessage | None = None

    @classmethod
    def create(
        cls,
        item_id: str,
        message: MailMessage,
    ):
        return cls(
            id=item_id,
            created=datetime.now(UTC),
            message=message,
        )
    
    def ready(self) -> bool:

        if self.next_retry is None:
            return True

        return datetime.now(UTC) >= self.next_retry