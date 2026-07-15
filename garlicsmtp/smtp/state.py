"""
SMTP Session States.
"""

from enum import Enum, auto


class SMTPState(Enum):

    CONNECT = auto()

    GREETING = auto()

    WAIT_EHLO = auto()

    WAIT_MAIL = auto()

    WAIT_RCPT = auto()

    WAIT_DATA = auto()

    RECEIVE_DATA = auto()

    QUEUED = auto()

    DELIVERY = auto()

    QUIT = auto()

    CLOSED = auto()
