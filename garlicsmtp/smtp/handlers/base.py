# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

"""
Base SMTP handler.
"""

from abc import ABC
from abc import abstractmethod


class SMTPHandler(ABC):

    @abstractmethod
    def handle(self, session, command):
        pass
