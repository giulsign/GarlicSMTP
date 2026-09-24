# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

"""
SMTP Finite State Machine.
"""

from garlicsmtp.smtp.state import SMTPState
from garlicsmtp.exceptions import SMTPProtocolError


class SMTPStateMachine:
    """
    Validates SMTP command sequences.
    """

    _allowed = {

        SMTPState.CONNECT: {
            "EHLO",
            "HELO",
            "QUIT",
        },

        SMTPState.WAIT_MAIL: {
            "MAIL",
            "RSET",
            "NOOP",
            "QUIT",
        },

        SMTPState.WAIT_RCPT: {
            "RCPT",
            "RSET",
            "NOOP",
            "QUIT",
        },

        SMTPState.WAIT_DATA: {
            "RCPT",
            "DATA",
            "RSET",
            "NOOP",
            "QUIT",
        },

        SMTPState.RECEIVE_DATA: set(),

    }

    @classmethod
    def validate(cls, session, command):

        allowed = cls._allowed.get(
            session.state,
            set()
        )

        if command.command not in allowed:

            raise SMTPProtocolError(
                f"Command {command.command} not allowed "
                f"in state {session.state.name}"
            )
