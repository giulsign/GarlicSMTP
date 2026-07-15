from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from garlicsmtp.core.events.base import BaseEvent
from garlicsmtp.models import MailMessage


@dataclass(slots=True)
class MailAcceptedEvent(BaseEvent):
    message: MailMessage

    @classmethod
    def from_message(cls, message: MailMessage):
        return cls(
            event_id=str(uuid4()),
            created=datetime.now(UTC),
            message=message,
        )