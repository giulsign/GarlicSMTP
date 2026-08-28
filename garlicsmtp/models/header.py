# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from dataclasses import dataclass
from dataclasses import field


@dataclass

class MailHeaders:

    fields: dict[str, str] = field(default_factory=dict)

    def add(self, key, value):

        self.fields[key] = value

    def get(self, key, default=None):

        return self.fields.get(key, default)
