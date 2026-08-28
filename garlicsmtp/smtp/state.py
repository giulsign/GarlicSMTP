# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

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
