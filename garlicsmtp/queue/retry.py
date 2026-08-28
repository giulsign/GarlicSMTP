# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from datetime import UTC, datetime, timedelta

class RetryPolicy:

    def __init__(
        self,
        base_delay=60,
        multiplier=2,
        max_delay=86400,
    ):
        self.base_delay = base_delay
        self.multiplier = multiplier
        self.max_delay = max_delay


    def next_retry(self, attempts):

        delay = self.base_delay * (
            self.multiplier ** max(0, attempts - 1)
        )

        delay = min(delay, self.max_delay)

        return datetime.now(UTC) + timedelta(
            seconds=delay,
        )

