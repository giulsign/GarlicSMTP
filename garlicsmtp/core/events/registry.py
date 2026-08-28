# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

class EventRegistry:

    def __init__(self):

        self.events = {}

    def register(self, event):

        self.events[event.__name__] = event

    def get(self, name):

        return self.events[name]
