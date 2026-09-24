# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from dataclasses import dataclass
from dataclasses import field


@dataclass

class MailHeaders:

    fields: dict[str, str] = field(default_factory=dict)

    def add(
        self,
        key: str,
        value: str,
    ):
        key_lower = key.lower()

        for existing_key in self.fields:
            if existing_key.lower() == key_lower:
                self.fields[existing_key] = value
                return

        self.fields[key] = value

    def get(
        self,
        key: str,
        default=None,
    ):
        key_lower = key.lower()

        for name, value in self.fields.items():
            if name.lower() == key_lower:
                return value

        return default
