# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from dataclasses import dataclass, field
from datetime import UTC, datetime

from garlicsmtp.models import MailMessage


@dataclass(slots=True)
class MessageEntry:

    id: str

    mailbox: str

    uid: int

    message: MailMessage

    internal_date: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    flags: set[str] = field(
        default_factory=set
    )