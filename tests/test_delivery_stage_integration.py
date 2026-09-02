# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.core.pipeline import Pipeline
from garlicsmtp.core.pipeline import PipelineContext
from garlicsmtp.queue.manager import QueueManager
from garlicsmtp.queue.stage import QueueStage
from garlicsmtp.storage.delivery_stage import DeliveryStage
from garlicsmtp.storage.store import MessageStore
from garlicsmtp.storage.entry import VerificationStatus


def test_pipeline_delivers_local_message(
    message,
):

    message.envelope.recipients = [
        "bob@test.onion"
    ]

    store = MessageStore()

    queue = QueueManager()

    pipeline = Pipeline()

    pipeline.add(
        DeliveryStage(
            store=store,
            queue_stage=QueueStage(queue),
            local_domains={
                "test.onion",
            },
        )
    )

    pipeline.execute(
        PipelineContext(
            message=message,
        )
    )

    ids = store.list_messages(
        "bob@test.onion"
    )

    assert len(ids) == 1

    assert queue.size() == 0


def test_pipeline_preserves_verified_status_for_local_message(
    message,
):
    message.envelope.recipients = [
        "bob@test.onion"
    ]

    store = MessageStore()
    queue = QueueManager()

    pipeline = Pipeline()
    pipeline.add(
        DeliveryStage(
            store=store,
            queue_stage=QueueStage(queue),
            local_domains={
                "test.onion",
            },
        )
    )

    pipeline.execute(
        PipelineContext(
            message=message,
            verification_status=(
                VerificationStatus.VERIFIED
            ),
        )
    )

    ids = store.list_messages(
        "bob@test.onion"
    )

    assert len(ids) == 1

    entry = store.get_entry(
        "bob@test.onion",
        ids[0],
    )

    assert entry is not None
    assert entry.verification_status == (
        VerificationStatus.VERIFIED
    )

    assert queue.size() == 0