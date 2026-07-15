from garlicsmtp.queue.item import QueueItem
from garlicsmtp.transport.base import Transport


class TransportManager:

    def __init__(
        self,
        default_transport: Transport,
        smtp_transport: Transport | None = None,
        local_transport: Transport | None = None,
    ):
        self.default_transport = default_transport
        self.smtp_transport = smtp_transport
        self.local_transport = local_transport

    def select_transport(self, item: QueueItem) -> Transport:
        recipient = item.message.envelope.recipients[0]

        if recipient.endswith(".onion"):
            return self.default_transport

        if recipient.endswith("@localhost") and self.local_transport:
            return self.local_transport

        if self.smtp_transport:
            return self.smtp_transport

        return self.default_transport

    def deliver(self, item: QueueItem) -> bool:
        transport = self.select_transport(item)
        return transport.deliver(item)