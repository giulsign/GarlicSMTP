from garlicsmtp.core.pipeline import PipelineContext
from garlicsmtp.queue.manager import QueueManager
from garlicsmtp.queue.stage import QueueStage


def test_queue_stage(message):

    queue = QueueManager()

    stage = QueueStage(queue)

    context = PipelineContext(message)

    stage.process(context)

    assert queue.size() == 1

    item = queue.dequeue()

    assert item.message is message