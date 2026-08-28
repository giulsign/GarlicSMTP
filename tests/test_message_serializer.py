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