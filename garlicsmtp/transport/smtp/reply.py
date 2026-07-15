from dataclasses import dataclass


@dataclass(slots=True)
class SMTPServerReply:

    code: int

    message: str 