import json
from datetime import datetime

from garlicsmtp.storage.entry import MessageEntry
from garlicsmtp.storage.serializer import MessageSerializer


class MessageEntrySerializer:

    @staticmethod
    def to_dict(
        entry: MessageEntry,
    ) -> dict:
        return {
            "id": entry.id,
            "mailbox": entry.mailbox,
            "uid": entry.uid,
            "internal_date": (
                entry.internal_date.isoformat()
            ),
            "flags": sorted(entry.flags),
            "message": MessageSerializer.to_dict(
                entry.message
            ),
        }

    @staticmethod
    def to_json(
        entry: MessageEntry,
    ) -> str:
        return json.dumps(
            MessageEntrySerializer.to_dict(
                entry
            ),
            indent=4,
            ensure_ascii=False,
        )

    @staticmethod
    def from_dict(
        data: dict,
    ) -> MessageEntry:
        return MessageEntry(
            id=data["id"],
            mailbox=data["mailbox"],
            uid=data["uid"],
            internal_date=datetime.fromisoformat(
                data["internal_date"]
            ),
            flags=set(
                data.get("flags", [])
            ),
            message=MessageSerializer.from_dict(
                data["message"]
            ),
        )

    @staticmethod
    def from_json(
        text: str,
    ) -> MessageEntry:
        return MessageEntrySerializer.from_dict(
            json.loads(text)
        )