# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.queue.item import QueueItem
from garlicsmtp.queue.serializer import QueueSerializer
from datetime import UTC, datetime
from garlicsmtp.queue.factory import QueueFactory


def test_queue_serializer(message):

    item = QueueItem.create(

        "ABC123",

        message

    )

    text = QueueSerializer.to_json(item)

    restored = QueueSerializer.from_json(text)

    assert restored.id == item.id

    assert restored.attempts == item.attempts

    assert restored.message.envelope.sender == item.message.envelope.sender


def test_queue_serializer_preserves_retry_fields(message):

    item = QueueFactory.create(message)

    item.attempts = 3
    item.next_retry = datetime(2026, 1, 1, tzinfo=UTC)
    item.last_error = "temporary failure"

    text = QueueSerializer.to_json(item)

    restored = QueueSerializer.from_json(text)

    assert restored.attempts == 3
    assert restored.next_retry == datetime(2026, 1, 1, tzinfo=UTC)
    assert restored.last_error == "temporary failure"