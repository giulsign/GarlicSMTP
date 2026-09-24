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
        lines = self.message.splitlines()

        if len(lines) == 1:
            return (
                f"{self.code} {lines[0]}\r\n"
                .encode("ascii")
            )

        serialized = []

        for line in lines[:-1]:
            serialized.append(
                f"{self.code}-{line}\r\n"
            )

        serialized.append(
            f"{self.code} {lines[-1]}\r\n"
        )

        return "".join(
            serialized
        ).encode("ascii")