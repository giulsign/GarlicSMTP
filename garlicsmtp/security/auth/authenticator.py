from abc import ABC, abstractmethod


class Authenticator(ABC):

    @abstractmethod
    def authenticate(
        self,
        username: str,
        password: str,
    ) -> bool:
        raise NotImplementedError