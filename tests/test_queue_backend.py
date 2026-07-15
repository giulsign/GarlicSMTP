from garlicsmtp.queue.backend import QueueBackend
from garlicsmtp.queue.manager import QueueManager


class SpyBackend(QueueBackend):

    def __init__(self):
        self.calls = []

    def enqueue(self, item):
        self.calls.append(("enqueue", item))

    def dequeue(self):
        self.calls.append(("dequeue",))
        return None

    def peek(self):
        self.calls.append(("peek",))
        return None

    def ack(self, item):
        self.calls.append(("ack", item))
        return True

    def nack(self, item):
        self.calls.append(("nack", item))
        return True

    def size(self):
        self.calls.append(("size",))
        return 0

    def empty(self):
        self.calls.append(("empty",))
        return True
    
    def update(self, item):
        self.calls.append(("update", item))
        return True


def test_queue_manager_delegates_to_backend():

    backend = SpyBackend()

    queue = QueueManager(
        backend=backend,
    )

    marker = object()

    queue.enqueue(marker)
    queue.peek()
    queue.ack(marker)
    queue.nack(marker)
    queue.size()
    queue.empty()
    queue.update(marker)

    assert backend.calls == [
        ("enqueue", marker),
        ("peek",),
        ("ack", marker),
        ("nack", marker),
        ("size",),
        ("empty",),
        ("update", marker)
    ]