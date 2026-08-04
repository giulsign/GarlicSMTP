from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum


class ApplicationEventLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class ApplicationEventSource(Enum):
    APPLICATION = "application"
    SMTP = "smtp"
    IMAP = "imap"
    QUEUE = "queue"
    STORE = "store"
    TOR = "tor"


@dataclass(
    frozen=True,
    slots=True,
)
class ApplicationEvent:
    sequence: int
    timestamp: datetime
    source: ApplicationEventSource
    level: ApplicationEventLevel
    message: str

    @property
    def timestamp_text(
        self,
    ) -> str:
        return self.timestamp.astimezone().strftime(
            "%H:%M:%S"
        )

    @classmethod
    def create(
        cls,
        *,
        sequence: int,
        source: ApplicationEventSource,
        level: ApplicationEventLevel,
        message: str,
    ) -> "ApplicationEvent":
        return cls(
            sequence=sequence,
            timestamp=datetime.now(
                timezone.utc
            ),
            source=source,
            level=level,
            message=message,
        )
