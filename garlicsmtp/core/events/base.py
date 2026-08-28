# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4


@dataclass(slots=True)
class BaseEvent:

    event_id: str
    created: datetime

    @classmethod
    def create(cls):

        return cls(

            event_id=str(uuid4()),

            created=datetime.now()

        )
