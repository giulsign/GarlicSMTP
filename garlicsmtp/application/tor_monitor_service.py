# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import time
from collections.abc import Callable

from garlicsmtp.application.event_hub import (
    ApplicationEventHub,
)
from garlicsmtp.application.tor_status import (
    TorStatus,
)
from garlicsmtp.application.tor_status_provider import (
    TorStatusProvider,
)
from garlicsmtp.core.service import Service
from garlicsmtp.core.tickable import Tickable
from garlicsmtp.application.event import (
    ApplicationEventSource,
)
from garlicsmtp.application.event_service import (
    ApplicationEventService,
)


Clock = Callable[[], float]


class TorMonitorService(
    Service,
    Tickable,
):

    def __init__(
        self,
        *,
        provider: TorStatusProvider,
        event_hub: ApplicationEventHub,
        interval_seconds: float = 10.0,
        clock: Clock | None = None,
        event_service: ApplicationEventService | None = None,
    ) -> None:
        if interval_seconds <= 0:
            raise ValueError(
                "interval_seconds must be "
                "greater than zero"
            )

        self.provider = provider
        self.event_hub = event_hub

        self.interval_seconds = (
            interval_seconds
        )

        self.clock = (
            clock
            or time.monotonic
        )

        self.running = False

        self._status = (
            self.provider.initial_status()
        )

        self._last_refresh: float | None = (
            None
        )
        self.event_service = event_service

    @property
    def status(
        self,
    ) -> TorStatus:
        return self._status

    def start(
        self,
    ) -> None:
        if self.running:
            return

        self.running = True
        self._last_refresh = None

    def stop(
        self,
    ) -> None:
        if not self.running:
            return

        self.running = False

    def tick(
        self,
    ) -> None:
        if not self.running:
            return

        now = self.clock()

        if not self._refresh_due(
            now
        ):
            return

        self.refresh(
            now=now
        )

    def refresh(
        self,
        *,
        now: float | None = None,
    ) -> TorStatus:
        refreshed_at = (
            self.clock()
            if now is None
            else now
        )

        previous = self._status
        current = self.provider.snapshot()

        self._status = current
        self._last_refresh = refreshed_at

        if current != previous:
            self._record_status_change(
                previous,
                current,
            )

            if self.event_service is None:
                self.event_hub.publish()

        return current

    def _refresh_due(
        self,
        now: float,
    ) -> bool:
        if self._last_refresh is None:
            return True

        return (
            now - self._last_refresh
            >= self.interval_seconds
        )

    def _record_status_change(
        self,
        previous: TorStatus,
        current: TorStatus,
    ) -> None:
        if self.event_service is None:
            return

        if (
            current.ready
            and not previous.ready
        ):
            self.event_service.info(
                ApplicationEventSource.TOR,
                "Tor became ready",
            )

            return

        if (
            previous.ready
            and not current.ready
        ):
            self.event_service.warning(
                ApplicationEventSource.TOR,
                "Tor became unavailable",
            )

            return

        if (
            current.authenticated
            and not previous.authenticated
        ):
            self.event_service.info(
                ApplicationEventSource.TOR,
                "Tor Control authenticated with SAFECOOKIE",
            )

            return

        if (
            current.last_error
            != previous.last_error
            and current.last_error
        ):
            self.event_service.warning(
                ApplicationEventSource.TOR,
                "Tor status changed",
            )

            return

        self.event_service.info(
            ApplicationEventSource.TOR,
            "Tor status updated",
        )