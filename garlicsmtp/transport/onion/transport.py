# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.exceptions import (
    PermanentDeliveryError,
    TemporaryDeliveryError,
)
from garlicsmtp.network.socks5 import (
    Socks5Client,
    Socks5Connection,
)
from garlicsmtp.network.socks5.exceptions import (
    Socks5ConnectionError,
    Socks5HandshakeError,
)
from garlicsmtp.queue.item import QueueItem
from garlicsmtp.transport.base import Transport
from garlicsmtp.transport.onion.validator import OnionValidator
from garlicsmtp.transport.smtp.client import SMTPClient
from garlicsmtp.transport.smtp.connection import SMTPConnection
from garlicsmtp.transport.smtp.exceptions import SMTPClientError
from garlicsmtp.security.encryption_capability import (
    EncryptionCapability,
)


class OnionTransport(Transport):

    def __init__(
        self,
        socks_client: Socks5Client | None = None,
        socks_host: str = "127.0.0.1",
        socks_port: int = 9050,
        destination_port: int = 25,
        smtp_client_factory=None,
        e2ee_capability_callback=None,
    ):
        self.validator = OnionValidator()
        self.destination_port = destination_port

        self.socks_client = socks_client or Socks5Client(
            Socks5Connection(
                proxy_host=socks_host,
                proxy_port=socks_port,
            )
        )

        self.smtp_client_factory = (
            smtp_client_factory
            or self._build_smtp_client
        )

        self.e2ee_capability_callback = (
            e2ee_capability_callback
        )

    def deliver(self, item: QueueItem) -> bool:
        message = item.message

        if message is None:
            raise PermanentDeliveryError(
                "Queue item has no message"
            )

        recipients = message.envelope.recipients

        if not recipients:
            raise PermanentDeliveryError(
                "Message has no recipients"
            )

        try:
            addresses = [
                self.validator.resolve(recipient)
                for recipient in recipients
            ]
        except ValueError as exc:
            raise PermanentDeliveryError(
                str(exc)
            ) from exc

        destination_host = addresses[0].hostname

        if any(
            address.hostname != destination_host
            for address in addresses
        ):
            raise PermanentDeliveryError(
                "Recipients for different onion hosts "
                "must be queued separately"
            )

        socks_connection = None

        try:
            socks_connection = self.socks_client.connect(
                destination_host,
                self.destination_port,
            )

            smtp_client = self.smtp_client_factory(
                socks_connection,
            )

            capability = (
                smtp_client.discover_e2ee_capability()
            )

            if capability is not None:
                try:
                    parsed_capability = (
                        EncryptionCapability.parse(
                            capability
                        )
                    )
                except ValueError as exc:
                    raise TemporaryDeliveryError(
                        "Invalid E2EE capability"
                    ) from exc

                if (
                    self.e2ee_capability_callback
                    is not None
                ):
                    try:
                        self.e2ee_capability_callback(
                            destination_host,
                            parsed_capability,
                        )
                    except ValueError as exc:
                        raise TemporaryDeliveryError(
                            "E2EE key rejected"
                        ) from exc

            delivered = smtp_client.deliver(
                message,
            )

            return delivered

        except (
            Socks5ConnectionError,
            Socks5HandshakeError,
            SMTPClientError,
            OSError,
            TimeoutError,
        ) as exc:
            raise TemporaryDeliveryError(
                f"Onion delivery failed: {exc}"
            ) from exc

        finally:
            if socks_connection is not None:
                socks_connection.close()

    def _build_smtp_client(
        self,
        socks_connection: Socks5Connection,
    ) -> SMTPClient:
        smtp_connection = SMTPConnection(
            connected_socket=socks_connection.socket,
        )

        return SMTPClient(
            connection=smtp_connection,
        )