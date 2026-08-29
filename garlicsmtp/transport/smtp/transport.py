# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.queue.item import QueueItem
from garlicsmtp.transport.base import Transport
from garlicsmtp.transport.dns import DNSResolver
from garlicsmtp.transport.smtp.connection import SMTPConnection
from garlicsmtp.transport.smtp.exceptions import SMTPClientError
from garlicsmtp.transport.smtp.protocol import SMTPClientProtocol


class SMTPTransport(Transport):

    def __init__(self):
        self.resolver = DNSResolver()
        self.connection_factory = SMTPConnection

    def deliver(self, item: QueueItem) -> bool:
        recipient = item.message.envelope.recipients[0]
        domain = recipient.split("@")[1]

        mx_records = self.resolver.lookup_mx(domain)
        mx = mx_records[0]

        connection = self.connection_factory()
        connection.connect(mx.exchange, 25)

        protocol = SMTPClientProtocol(connection)

        greeting = protocol.read_reply()

        if greeting.code != 220:
            raise SMTPClientError(
                f"SMTP greeting failed ({greeting.code})"
            )

        protocol.ehlo("[127.0.0.1]")

        protocol.mail_from(
            item.message.envelope.sender
        )

        for recipient in item.message.envelope.recipients:
            protocol.rcpt_to(recipient)

        protocol.data(
            item.message.body
        )

        protocol.quit()

        connection.close()

        return True