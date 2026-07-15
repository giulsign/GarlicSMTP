from dataclasses import dataclass, field


@dataclass

class Envelope:

    sender: str = ""

    recipients: list[str] = field(default_factory=list)
