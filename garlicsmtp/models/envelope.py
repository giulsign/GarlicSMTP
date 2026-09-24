# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from dataclasses import dataclass, field


@dataclass

class Envelope:

    sender: str = ""

    recipients: list[str] = field(default_factory=list)
