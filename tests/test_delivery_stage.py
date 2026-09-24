# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.queue.manager import QueueManager
from garlicsmtp.queue.stage import QueueStage
from garlicsmtp.storage.delivery_stage import (
    DeliveryStage,
)

from garlicsmtp.storage.store import (
    MessageStore,
)
from garlicsmtp.core.pipeline import PipelineContext
from garlicsmtp.storage.entry import (
    VerificationStatus,
)
from unittest.mock import Mock


def test_delivery_stage_stores_local_message(
    message,
):

    message.envelope.recipients = [
        "bob@example.onion"
    ]

    store = MessageStore()

    queue = QueueManager()

    stage = DeliveryStage(
        store=store,
        queue_stage=QueueStage(queue),
        local_domains={
            "example.onion",
        },
    )

    context = PipelineContext(
        message=message,
    )

    stage.process(context)

    ids = store.list_messages(
        "bob@example.onion"
    )

    assert len(ids) == 1

    stored = store.get(
        "bob@example.onion",
        ids[0],
    )

    assert stored is message

    assert queue.size() == 0


def test_delivery_stage_queues_remote_message(
    message,
):

    message.envelope.recipients = [
        "bob@remote.onion"
    ]

    store = MessageStore()

    queue = QueueManager()

    stage = DeliveryStage(
        store=store,
        queue_stage=QueueStage(queue),
        local_domains={
            "example.onion",
        },
    )

    context = PipelineContext(
        message=message,
    )

    stage.process(context)

    assert queue.size() == 1

    assert store.list_messages(
        "bob@remote.onion"
    ) == []


def test_delivery_stage_preserves_verification_status(
    message,
):
    store = MessageStore()

    queue_stage = Mock()

    stage = DeliveryStage(
        store=store,
        queue_stage=queue_stage,
        local_domains={"test.onion"},
    )

    context = PipelineContext(
        message=message,
        verification_status=(
            VerificationStatus.VERIFIED
        ),
    )

    result = stage.process(context)

    entries = store.list_entries(
        "bob@test.onion"
    )

    assert result is context
    assert len(entries) == 1
    assert (
        entries[0].verification_status
        == VerificationStatus.VERIFIED
    )

    queue_stage.process.assert_not_called()