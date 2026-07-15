from dataclasses import dataclass
from datetime import datetime, UTC




@dataclass

class Metadata:

    received = datetime.now(UTC)

    queue_id = ""

    retries = 0

    transport = "onion"

    size = 0
