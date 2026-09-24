# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from abc import ABC, abstractmethod

from garlicsmtp.queue.item import QueueItem

class Transport:

    def deliver(self, item) -> bool:
        """
        Returns:
            True  -> delivery completed.
            False -> temporary failure.
        Raises:
            Exception -> unexpected failure.
        """
        raise NotImplementedError