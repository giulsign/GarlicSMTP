import json
from dataclasses import asdict

from garlicsmtp.models import (
    Envelope,
    MailHeaders,
    MailMessage,
    Metadata,
)


class MessageSerializer:

    @staticmethod
    def to_dict(
        message: MailMessage,
    ) -> dict:
        return asdict(message)

    @staticmethod
    def to_json(
        message: MailMessage,
    ) -> str:
        return json.dumps(
            MessageSerializer.to_dict(message),
            indent=4,
            ensure_ascii=False,
        )

    @staticmethod
    def from_dict(
        data: dict,
    ) -> MailMessage:
        return MailMessage(
            envelope=Envelope(
                **data["envelope"]
            ),
            headers=MailHeaders(
                **data["headers"]
            ),
            metadata=Metadata(
                **data["metadata"]
            ),
            body=data["body"],
        )

    @staticmethod
    def from_json(
        text: str,
    ) -> MailMessage:
        return MessageSerializer.from_dict(
            json.loads(text)
        )