# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from collections import defaultdict

from garlicsmtp.core.events.base import BaseEvent


class EventBus:

    def __init__(self):

        self._handlers = defaultdict(list)

    def subscribe(self, event_type, handler):

        self._handlers[event_type].append(handler)

    def publish(self, event: BaseEvent):

        handlers = self._handlers[type(event)]

        for handler in handlers:

            handler.handle(event)
