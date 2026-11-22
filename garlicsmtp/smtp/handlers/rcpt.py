# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.smtp.handlers.base import SMTPHandler
from garlicsmtp.smtp.replies import ReplyFactory
from garlicsmtp.smtp.state import SMTPState


class RCPTHandler(SMTPHandler):

    def __init__(
        self,
        address_policy=None,
    ):
        self.address_policy = address_policy

    def handle(self, session, command):
        recipient = command.arguments["to"]
        if session.message.envelope.recipients:
            return ReplyFactory.bad_sequence()

        if (
            self.address_policy is not None
            and not self.address_policy.allows_incoming_recipient(
                recipient
            )
        ):
            return ReplyFactory.mailbox_unavailable()

        session.message.envelope.recipients.append(recipient)

        session.state = SMTPState.WAIT_DATA

        return ReplyFactory.ok("Recipient OK")