from abc import ABC, abstractmethod

from garlicsmtp.network.text import TextConnection


class IMAPResponse(ABC):

    @abstractmethod
    def send(
        self,
        connection: TextConnection,
    ) -> None:
        raise NotImplementedError