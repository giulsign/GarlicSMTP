from collections import deque

from garlicsmtp.queue.backend import QueueBackend


class MemoryQueueBackend(QueueBackend):

    def __init__(self):

        self.queue = deque()

    def enqueue(self, item):

        self.queue.append(item)

    def dequeue(self):
        #
        # Legacy API.
        # New code should use peek() + ack().
        #

        if not self.queue:

            return None

        return self.queue.popleft()

    def size(self):

        return len(self.queue)
    
    def empty(self):
        return not self.queue


    def peek(self):
        if self.empty():
            return None

        return self.queue[0]
    
    def ack(self, item):
        if self.empty():
            return False

        if self.queue[0] is not item:
            return False

        self.queue.popleft()

        return True
    
    def nack(self, item):
        return True
    

    def update(self, item):
        return True
