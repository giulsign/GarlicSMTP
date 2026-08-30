# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from datetime import UTC, datetime

from garlicsmtp.storage.entry import MessageEntry
from garlicsmtp.storage.entry_serializer import (
    MessageEntrySerializer,
)
from garlicsmtp.storage.entry import (
    VerificationStatus,
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


def test_message_entry_serializes_verification_status(
    message,
):
    entry = MessageEntry(
        id="message-id",
        mailbox="bob@test.onion",
        uid=7,
        message=message,
        verification_status=(
            VerificationStatus.VERIFIED
        ),
    )

    data = MessageEntrySerializer.to_dict(
        entry
    )

    assert data["verification_status"] == (
        "verified"
    )


def test_message_entry_legacy_data_defaults_to_unsigned(
    message,
):
    entry = MessageEntry(
        id="message-id",
        mailbox="bob@test.onion",
        uid=7,
        message=message,
    )

    data = MessageEntrySerializer.to_dict(
        entry
    )

    data.pop(
        "verification_status",
        None,
    )

    restored = MessageEntrySerializer.from_dict(
        data
    )

    assert restored.verification_status == (
        VerificationStatus.UNSIGNED
    )