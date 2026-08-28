# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from dataclasses import dataclass, field


@dataclass(slots=True)
class SMTPCommand:
    command: str
    arguments: dict[str, str] = field(default_factory=dict)
    raw: str = ""


@dataclass(slots=True)
class SMTPReply:
    code: int
    message: str

    def serialize(self) -> bytes:
        return f"{self.code} {self.message}\r\n".encode("ascii")