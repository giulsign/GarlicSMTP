from dataclasses import dataclass, field
from datetime import datetime, UTC


@dataclass
class Metadata:
    received: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )
    queue_id: str = ""
    retries: int = 0
    transport: str = "onion"
    size: int = 0