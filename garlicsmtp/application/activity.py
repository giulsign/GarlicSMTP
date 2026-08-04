from dataclasses import dataclass

from garlicsmtp.application.event import (
    ApplicationEvent,
    ApplicationEventLevel,
    ApplicationEventSource,
)


@dataclass(
    frozen=True,
    slots=True,
)
class ApplicationActivityEntry:

    sequence: int
    timestamp_text: str
    source_text: str
    level_text: str
    status_key: str
    icon_text: str
    short_text: str
    details: str | None = None


class ApplicationActivityFormatter:

    SOURCE_LABELS = {
        ApplicationEventSource.APPLICATION: (
            "Application"
        ),
        ApplicationEventSource.SMTP: "SMTP",
        ApplicationEventSource.IMAP: "IMAP",
        ApplicationEventSource.QUEUE: "Queue",
        ApplicationEventSource.STORE: "Store",
        ApplicationEventSource.TOR: "Tor",
    }

    LEVEL_LABELS = {
        ApplicationEventLevel.INFO: "Info",
        ApplicationEventLevel.WARNING: (
            "Warning"
        ),
        ApplicationEventLevel.ERROR: "Error",
    }

    STATUS_KEYS = {
        ApplicationEventLevel.INFO: (
            "running"
        ),
        ApplicationEventLevel.WARNING: (
            "starting"
        ),
        ApplicationEventLevel.ERROR: (
            "stopped"
        ),
    }

    ICONS = {
        ApplicationEventLevel.INFO: "●",
        ApplicationEventLevel.WARNING: (
            "▲"
        ),
        ApplicationEventLevel.ERROR: "■",
    }

    def format(
        self,
        event: ApplicationEvent,
    ) -> ApplicationActivityEntry:
        return ApplicationActivityEntry(
            sequence=event.sequence,
            timestamp_text=(
                event.timestamp_text
            ),
            source_text=(
                self.SOURCE_LABELS[
                    event.source
                ]
            ),
            level_text=(
                self.LEVEL_LABELS[
                    event.level
                ]
            ),
            status_key=(
                self.STATUS_KEYS[
                    event.level
                ]
            ),
            icon_text=(
                self.ICONS[
                    event.level
                ]
            ),
            short_text=event.message,
            details=None,
        )

    def format_many(
        self,
        events: tuple[
            ApplicationEvent,
            ...,
        ],
    ) -> tuple[
        ApplicationActivityEntry,
        ...,
    ]:
        return tuple(
            self.format(event)
            for event in events
        )
