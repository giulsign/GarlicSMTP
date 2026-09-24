# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.storage.serializer import (
    MessageSerializer,
)


def test_message_serializer_roundtrip(
    message,
):
    message.headers.fields[
        "Subject"
    ] = "Stored message"

    message.body = "Mailbox body"

    text = MessageSerializer.to_json(
        message
    )

    restored = MessageSerializer.from_json(
        text
    )

    assert (
        restored.envelope.sender
        == message.envelope.sender
    )

    assert (
        restored.envelope.recipients
        == message.envelope.recipients
    )

    assert (
        restored.headers.fields
        == message.headers.fields
    )

    assert restored.body == message.body


def test_message_serializer_omits_legacy_metadata(
    message,
):
    data = MessageSerializer.to_dict(
        message
    )

    assert "metadata" not in data


def test_message_serializer_reads_legacy_metadata(
    message,
):
    data = MessageSerializer.to_dict(
        message
    )

    data["metadata"] = {
        "queue_id": "legacy-queue-id",
        "retries": 7,
        "transport": "legacy-transport",
        "size": 4096,
        "received": (
            "2026-08-28T21:00:00+00:00"
        ),
    }

    restored = MessageSerializer.from_dict(
        data
    )

    assert (
        restored.envelope.sender
        == message.envelope.sender
    )

    assert (
        restored.envelope.recipients
        == message.envelope.recipients
    )

    assert not hasattr(
        restored,
        "metadata",
    )