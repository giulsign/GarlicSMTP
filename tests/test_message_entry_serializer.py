from datetime import UTC, datetime

from garlicsmtp.storage.entry import MessageEntry
from garlicsmtp.storage.entry_serializer import (
    MessageEntrySerializer,
)


def test_message_entry_serializer_roundtrip(
    message,
):

    entry = MessageEntry(
        id="message-id",
        mailbox="bob@test.onion",
        uid=7,
        internal_date=datetime(
            2030,
            1,
            2,
            3,
            4,
            5,
            tzinfo=UTC,
        ),
        flags={
            "\\Seen",
            "\\Flagged",
        },
        message=message,
    )

    text = MessageEntrySerializer.to_json(
        entry
    )

    restored = (
        MessageEntrySerializer.from_json(
            text
        )
    )

    assert restored.id == entry.id
    assert restored.mailbox == entry.mailbox
    assert restored.uid == 7
    assert (
        restored.internal_date
        == entry.internal_date
    )
    assert restored.flags == entry.flags

    assert (
        restored.message.envelope.sender
        == message.envelope.sender
    )

    assert (
        restored.message.envelope.recipients
        == message.envelope.recipients
    )