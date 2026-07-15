from abc import ABC
from abc import abstractmethod

from garlicsmtp.core.events.base import BaseEvent


class EventHandler(ABC):

    @abstractmethod
    def handle(self, event: BaseEvent):

        pass
