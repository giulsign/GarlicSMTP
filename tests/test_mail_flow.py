from garlicsmtp.core.pipeline import (
    LoggerStage,
    Pipeline,
)
from garlicsmtp.queue.factory import (
    QueueFactory,
)
from garlicsmtp.queue.manager import (
    QueueManager,
)
from garlicsmtp.queue.stage import (
    QueueStage,
)
from garlicsmtp.queue.worker import (
    QueueWorker,
)
from garlicsmtp.smtp.connection import (
    SMTPConnection,
)
from garlicsmtp.smtp.protocol import (
    SMTPProtocol,
)
from garlicsmtp.transport.base import (
    Transport,
)
from garlicsmtp.transport.dummy import (
    DummyTransport,
)
from garlicsmtp.transport.manager import (
    TransportManager,
)


class SpyTransport(Transport):

    def __init__(self):
        self.delivered = []

    def deliver(self, item):
        self.delivered.append(
            item
        )

        return True


class FakeSocket:

    def __init__(self):
        self.sent = b""

        self.buffer = [
            b"EHLO client.onion\r\n",
            b"MAIL FROM:<alice@test.onion>\r\n",
            b"RCPT TO:<bob@test.onion>\r\n",
            b"DATA\r\n",
            b"Subject: Flow Test\r\n",
            b"\r\n",
            b"Hello Flow\r\n",
            b".\r\n",
            b"QUIT\r\n",
        ]

    def sendall(self, data):
        self.sent += data

    def recv(self, size):
        if self.buffer:
            return self.buffer.pop(0)

        return b""

    def close(self):
        pass


def build_queue_pipeline() -> tuple[
    Pipeline,
    QueueManager,
]:
    queue = QueueManager()

    pipeline = Pipeline()
    pipeline.add(
        QueueStage(queue)
    )

    return pipeline, queue


def test_mail_flows_from_queue_to_transport(
    message,
):
    queue = QueueManager()

    transport = TransportManager(
        default_transport=DummyTransport(),
    )

    worker = QueueWorker(
        queue=queue,
        transport=transport,
    )

    item = QueueFactory.create(
        message
    )

    queue.enqueue(
        item
    )

    assert queue.size() == 1

    worker.start()
    worker.tick()
    worker.stop()

    assert queue.size() == 0


def test_worker_delivers_correct_item(
    message,
):
    queue = QueueManager()

    spy = SpyTransport()

    transport = TransportManager(
        default_transport=spy,
    )

    worker = QueueWorker(
        queue=queue,
        transport=transport,
    )

    item = QueueFactory.create(
        message
    )

    queue.enqueue(
        item
    )

    worker.start()
    worker.tick()
    worker.stop()

    assert len(spy.delivered) == 1
    assert spy.delivered[0] is item


def test_smtp_protocol_queues_message():
    sock = FakeSocket()

    connection = SMTPConnection(
        sock,
        ("127.0.0.1", 2525),
    )

    pipeline, queue = (
        build_queue_pipeline()
    )

    protocol = SMTPProtocol(
        connection,
        hostname="garlicsmtp.local",
        pipeline=pipeline,
    )

    protocol.serve()

    assert queue.size() == 1

    item = queue.dequeue()

    assert (
        item.message.envelope.sender
        == "alice@test.onion"
    )

    assert (
        item.message.envelope.recipients
        == [
            "bob@test.onion",
        ]
    )

    assert (
        item.message.headers.get(
            "Subject"
        )
        == "Flow Test"
    )

    assert (
        item.message.body
        == "Hello Flow"
    )


def test_full_internal_mail_flow():
    queue = QueueManager()

    pipeline = Pipeline()
    pipeline.add(
        LoggerStage()
    )
    pipeline.add(
        QueueStage(queue)
    )

    sock = FakeSocket()

    connection = SMTPConnection(
        sock,
        ("127.0.0.1", 2525),
    )

    protocol = SMTPProtocol(
        connection,
        hostname="garlicsmtp.local",
        pipeline=pipeline,
    )

    protocol.serve()

    assert queue.size() == 1

    spy = SpyTransport()

    transport = TransportManager(
        default_transport=spy,
    )

    worker = QueueWorker(
        queue=queue,
        transport=transport,
    )

    worker.start()
    worker.tick()
    worker.stop()

    assert queue.size() == 0
    assert len(spy.delivered) == 1

    item = spy.delivered[0]

    assert (
        item.message.envelope.sender
        == "alice@test.onion"
    )

    assert (
        item.message.envelope.recipients
        == [
            "bob@test.onion",
        ]
    )

    assert (
        item.message.headers.get(
            "Subject"
        )
        == "Flow Test"
    )

    assert (
        item.message.body
        == "Hello Flow"
    )