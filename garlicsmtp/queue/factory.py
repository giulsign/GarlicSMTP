# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from datetime import datetime, UTC
from uuid import uuid4

from garlicsmtp.models import MailMessage

from .item import QueueItem


class QueueFactory:
    @staticmethod
    def create(message: MailMessage) -> QueueItem:
        return QueueItem(
            id=str(uuid4()),
            created=datetime.now(UTC),
            attempts=0,
            next_retry=None,
            message=message,
        )