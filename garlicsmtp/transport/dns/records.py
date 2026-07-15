from dataclasses import dataclass


@dataclass(slots=True)
class MXRecord:
    priority: int
    exchange: str