"""
Base SMTP handler.
"""

from abc import ABC
from abc import abstractmethod


class SMTPHandler(ABC):

    @abstractmethod
    def handle(self, session, command):
        pass
