from garlicsmtp.queue.memory import MemoryQueueBackend

from collections import deque

class QueueManager:

    def __init__(self, backend=None):
        self.backend = backend or MemoryQueueBackend()

    def enqueue(self, item):
        return self.backend.enqueue(item)

    def peek(self):
        return self.backend.peek()

    def ack(self, item):
        return self.backend.ack(item)

    def nack(self, item):
        return self.backend.nack(item)

    def dequeue(self):
        #
        # Legacy API.
        # New code should use peek() + ack().
        #
        return self.backend.dequeue()

    def size(self):
        return self.backend.size()

    def empty(self):
        return self.backend.empty()
    
    def update(self, item):
        return self.backend.update(item)
