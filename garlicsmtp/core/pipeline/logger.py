from .stage import PipelineStage


class LoggerStage(PipelineStage):

    def process(self, context):

        print(
            "PIPELINE",
            context.message.envelope.sender,
            "->",
            context.message.envelope.recipients,
        )