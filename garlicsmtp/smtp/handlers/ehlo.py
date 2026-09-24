# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.smtp.handlers.base import SMTPHandler
from garlicsmtp.smtp.replies import ReplyFactory
from garlicsmtp.smtp.state import SMTPState


class EHLOHandler(SMTPHandler):

    def __init__(
        self,
        e2ee_capability: str | None = None,
    ):
        self.e2ee_capability = e2ee_capability

    def handle(self, session, command):
        session.helo = command.arguments["domain"]
        session.state = SMTPState.WAIT_MAIL

        message = f"Hello {session.helo}"

        if self.e2ee_capability is not None:
            message += (
                "\nGARLICSMTP-E2EE "
                + self.e2ee_capability
            )

        return ReplyFactory.ok(
            message
        )
