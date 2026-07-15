from garlicsmtp.core.pipeline import Pipeline, PipelineContext, LoggerStage
from garlicsmtp.queue.manager import QueueManager
from garlicsmtp.queue.serializer import QueueSerializer
from garlicsmtp.queue.stage import QueueStage
from garlicsmtp.queue.worker import QueueWorker
from garlicsmtp.transport.local.transport import LocalTransport
from garlicsmtp.transport.manager import TransportManager


def test_end_to_end(tmp_path, message):

    queue = QueueManager()

    pipeline = Pipeline()
    pipeline.add(LoggerStage())
    pipeline.add(QueueStage(queue))

    context = PipelineContext(message)

    pipeline.execute(context)

    assert queue.size() == 1

    transport = LocalTransport(tmp_path)
    manager = TransportManager(transport)

    worker = QueueWorker(
        queue,
        manager,
    )

    assert worker.process() is True

    assert queue.size() == 0

    files = list(tmp_path.glob("*.json"))

    assert len(files) == 1

    loaded = QueueSerializer.from_json(
        files[0].read_text(encoding="utf-8")
    )

    assert loaded.id

    assert loaded.message.envelope.sender == (
        message.envelope.sender
    )

    assert loaded.message.envelope.recipients == (
        message.envelope.recipients
    )

    assert loaded.message.headers.fields == (
        message.headers.fields
    )

    assert loaded.message.body == (
        message.body
    )