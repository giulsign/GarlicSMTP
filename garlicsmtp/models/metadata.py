# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from dataclasses import dataclass, field
from datetime import datetime, UTC


@dataclass
class Metadata:
    received: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )
    queue_id: str = ""
    retries: int = 0
    transport: str = "onion"
    size: int = 0