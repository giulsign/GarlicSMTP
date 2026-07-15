from garlicsmtp.core.pipeline.stage import PipelineStage
from garlicsmtp.queue.stage import QueueStage
from garlicsmtp.storage.store import MessageStore


class DeliveryStage(PipelineStage):

    def __init__(
        self,
        store: MessageStore,
        queue_stage: QueueStage,
        local_domains: set[str],
    ):
        self.store = store
        self.queue_stage = queue_stage
        self.local_domains = local_domains

    def process(self, context):
        message = context.message

        recipient = message.envelope.recipients[0]

        mailbox, domain = recipient.rsplit(
            "@",
            1,
        )

        if domain in self.local_domains:
            self.store.save(
                recipient,
                message,
            )

            return context

        return self.queue_stage.process(
            context
        )