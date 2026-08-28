# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from abc import ABC, abstractmethod


class QueueBackend(ABC):

    @abstractmethod
    def enqueue(self, item):
        pass

    @abstractmethod
    def peek(self):
        pass

    @abstractmethod
    def ack(self, item):
        pass

    @abstractmethod
    def nack(self, item):
        pass

    @abstractmethod
    #
    # Legacy API.
    # New code should use peek() + ack().
    #
    def dequeue(self):
        pass

    @abstractmethod
    def size(self):
        pass

    @abstractmethod
    def empty(self):
        pass

    @abstractmethod
    def update(self, item):
        """Persist changes made to an existing QueueItem."""
        pass