# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.smtp.handlers.base import SMTPHandler

from garlicsmtp.smtp.replies import ReplyFactory

from garlicsmtp.smtp.state import SMTPState


class MailHandler(SMTPHandler):

    def handle(self, session, command):

        session.message.envelope.sender = command.arguments["from"]

        session.state = SMTPState.WAIT_RCPT

        return ReplyFactory.ok(
            "Sender OK"
        )
