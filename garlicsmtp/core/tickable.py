from abc import ABC, abstractmethod


class Tickable(ABC):

    @abstractmethod
    def tick(self) -> None:
        raise NotImplementedError