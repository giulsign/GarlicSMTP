from garlicsmtp.queue.manager import QueueManager
from garlicsmtp.queue.stage import QueueStage
from garlicsmtp.storage.delivery_stage import (
    DeliveryStage,
)

from garlicsmtp.storage.store import (
    MessageStore,
)
from garlicsmtp.core.pipeline import PipelineContext


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