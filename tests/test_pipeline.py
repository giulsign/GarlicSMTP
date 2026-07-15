from garlicsmtp.core.pipeline import Pipeline
from garlicsmtp.core.pipeline import PipelineContext
from garlicsmtp.core.pipeline import LoggerStage

from garlicsmtp.models.envelope import Envelope
from garlicsmtp.models.header import MailHeaders
from garlicsmtp.models.metadata import Metadata
from garlicsmtp.models import MailMessage


def test_pipeline_logger():

    message = MailMessage(
        envelope=Envelope(
            sender="alice@test.onion",
            recipients=["bob@test.onion"]
        ),
        headers=MailHeaders(),
        metadata=Metadata()
    )

    pipeline = Pipeline()
    pipeline.add(LoggerStage())

    context = PipelineContext(message)

    pipeline.execute(context)

    assert context.message.envelope.sender == "alice@test.onion"

