from dataclasses import dataclass

from .envelope import Envelope
from .header import MailHeaders
from .metadata import Metadata


@dataclass

class MailMessage:

    envelope: Envelope

    headers: MailHeaders

    metadata: Metadata

    body: str = ""
