# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.smtp.handlers.base import SMTPHandler

from garlicsmtp.smtp.replies import ReplyFactory

from garlicsmtp.smtp.state import SMTPState


class RCPTHandler(SMTPHandler):

    def handle(self, session, command):

        session.message.envelope.recipients.append(command.arguments["to"])

        session.state = SMTPState.WAIT_DATA

        return ReplyFactory.ok(
            "Recipient OK"
        )
