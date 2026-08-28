# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import threading
from collections import deque
from collections.abc import Callable
from datetime import datetime, timezone

from garlicsmtp.application.event import (
    ApplicationEvent,
    ApplicationEventLevel,
    ApplicationEventSource,
)


EventClock = Callable[[], datetime]


class ApplicationEventLog:

    def __init__(
        self,
        *,
        capacity: int = 500,
        clock: EventClock | None = None,
    ) -> None:
        if capacity <= 0:
            raise ValueError(
                "capacity must be greater than zero"
            )

        self.capacity = capacity

        self.clock = (
            clock
            or self._utc_now
        )

        self._events: deque[
            ApplicationEvent
        ] = deque(
            maxlen=capacity
        )

        self._sequence = 0
        self._lock = threading.RLock()

    def record(
        self,
        *,
        source: ApplicationEventSource,
        level: ApplicationEventLevel,
        message: str,
    ) -> ApplicationEvent:
        normalized_message = (
            self._validate_message(
                message
            )
        )

        with self._lock:
            self._sequence += 1

            event = ApplicationEvent(
                sequence=self._sequence,
                timestamp=self.clock(),
                source=source,
                level=level,
                message=normalized_message,
            )

            self._events.append(
                event
            )

            return event

    def snapshot(
        self,
        *,
        newest_first: bool = False,
    ) -> tuple[ApplicationEvent, ...]:
        with self._lock:
            events = tuple(
                self._events
            )

        if newest_first:
            return tuple(
                reversed(events)
            )

        return events

    def clear(
        self,
    ) -> None:
        with self._lock:
            self._events.clear()

    def __len__(
        self,
    ) -> int:
        with self._lock:
            return len(
                self._events
            )

    @staticmethod
    def _validate_message(
        message: str,
    ) -> str:
        if not isinstance(
            message,
            str,
        ):
            raise TypeError(
                "event message must be text"
            )

        normalized = " ".join(
            message.split()
        )

        if not normalized:
            raise ValueError(
                "event message cannot be empty"
            )

        if len(normalized) > 500:
            normalized = (
                normalized[:497]
                + "..."
            )

        return normalized

    @staticmethod
    def _utc_now(
    ) -> datetime:
        return datetime.now(
            timezone.utc
        )
