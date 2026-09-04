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
    ):
        self.connection = connection
        self.protocol = SMTPClientProtocol(
            connection,
        )

    def discover_e2ee_capability(
        self,
    ) -> str | None:
        self.protocol.greeting()

        ehlo_reply = self.protocol.ehlo(
            "[127.0.0.1]",
        )

        self.e2ee_capability = (
            ehlo_reply.capability(
                "GARLICSMTP-E2EE"
            )
        )

        self._session_prepared = True

        return self.e2ee_capability

    def deliver(
        self,
        message: MailMessage,
    ) -> bool:
        if not getattr(
            self,
            "_session_prepared",
            False,
        ):
            self.discover_e2ee_capability()

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

        self._session_prepared = False

        return True

    @staticmethod
    def serialize_message(
        message: MailMessage,
    ) -> str:
        return MessageSerializer.to_rfc5322(
            message
        )