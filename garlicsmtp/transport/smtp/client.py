# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.models import MailMessage
from garlicsmtp.transport.smtp.connection import SMTPConnection
from garlicsmtp.transport.smtp.protocol import SMTPClientProtocol
from garlicsmtp.storage.serializer import MessageSerializer


class SMTPClient:

    def __init__(
        self,
        connection: SMTPConnection,
        hostname: str = "garlicsmtp.local",
    ):
        self.connection = connection
        self.hostname = hostname
        self.protocol = SMTPClientProtocol(
            connection,
        )

    def deliver(
        self,
        message: MailMessage,
    ) -> bool:
        self.protocol.greeting()

        self.protocol.ehlo(
            self.hostname,
        )

        self.protocol.mail_from(
            message.envelope.sender,
        )

        for recipient in message.envelope.recipients:
            self.protocol.rcpt_to(
                recipient,
            )

        self.protocol.data(
            self.serialize_message(message),
        )

        self.protocol.quit()

        return True

    @staticmethod
    def serialize_message(
        message: MailMessage,
    ) -> str:
        return MessageSerializer.to_rfc5322(
            message
        )