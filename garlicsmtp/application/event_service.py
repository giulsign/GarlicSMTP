# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.application.event import (
    ApplicationEvent,
    ApplicationEventLevel,
    ApplicationEventSource,
)
from garlicsmtp.application.event_hub import (
    ApplicationEventHub,
)
from garlicsmtp.application.event_log import (
    ApplicationEventLog,
)


class ApplicationEventService:

    def __init__(
        self,
        *,
        event_log: ApplicationEventLog,
        event_hub: ApplicationEventHub,
    ) -> None:
        self.event_log = event_log
        self.event_hub = event_hub

    def record(
        self,
        *,
        source: ApplicationEventSource,
        level: ApplicationEventLevel,
        message: str,
    ) -> ApplicationEvent:
        event = self.event_log.record(
            source=source,
            level=level,
            message=message,
        )

        self.event_hub.publish(
            event
        )

        return event

    def info(
        self,
        source: ApplicationEventSource,
        message: str,
    ) -> ApplicationEvent:
        return self.record(
            source=source,
            level=(
                ApplicationEventLevel.INFO
            ),
            message=message,
        )

    def warning(
        self,
        source: ApplicationEventSource,
        message: str,
    ) -> ApplicationEvent:
        return self.record(
            source=source,
            level=(
                ApplicationEventLevel.WARNING
            ),
            message=message,
        )

    def error(
        self,
        source: ApplicationEventSource,
        message: str,
    ) -> ApplicationEvent:
        return self.record(
            source=source,
            level=(
                ApplicationEventLevel.ERROR
            ),
            message=message,
        )
