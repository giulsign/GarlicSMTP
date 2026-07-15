from garlicsmtp.queue.item import QueueItem
from garlicsmtp.transport.base import Transport


class DummyOnionTransport(Transport):

    def __init__(self):
        self.delivered = []

    def deliver(self, item: QueueItem) -> bool:
        self.delivered.append(item)
        return True