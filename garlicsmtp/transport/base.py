from abc import ABC, abstractmethod

from garlicsmtp.queue.item import QueueItem

class Transport:

    def deliver(self, item) -> bool:
        """
        Returns:
            True  -> delivery completed.
            False -> temporary failure.
        Raises:
            Exception -> unexpected failure.
        """
        raise NotImplementedError