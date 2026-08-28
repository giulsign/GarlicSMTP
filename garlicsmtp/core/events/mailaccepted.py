# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from garlicsmtp.core.events.base import BaseEvent
from garlicsmtp.models import MailMessage


@dataclass(slots=True)
class MailAcceptedEvent(BaseEvent):
    message: MailMessage

    @classmethod
    def from_message(cls, message: MailMessage):
        return cls(
            event_id=str(uuid4()),
            created=datetime.now(UTC),
            message=message,
        )