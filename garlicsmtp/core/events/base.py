from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4


@dataclass(slots=True)
class BaseEvent:

    event_id: str
    created: datetime

    @classmethod
    def create(cls):

        return cls(

            event_id=str(uuid4()),

            created=datetime.now()

        )
