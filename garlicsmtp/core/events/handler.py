# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from abc import ABC
from abc import abstractmethod

from garlicsmtp.core.events.base import BaseEvent


class EventHandler(ABC):

    @abstractmethod
    def handle(self, event: BaseEvent):

        pass
