from garlicsmtp.core.engine import (
    Bootstrap,
    GarlicSMTPConfig,
)
from garlicsmtp.core.pipeline import (
    PipelineContext,
)


def test_receiver_pipeline_stores_local_mail(
    tmp_path,
    message,
):
    database = tmp_path / "mailboxes.db"

    config = GarlicSMTPConfig(
        hostname="receiver.onion",
        mailbox_db=str(database),
    )

    bootstrap = Bootstrap(
        config=config,
    )

    message.envelope.recipients = [
        "bob@receiver.onion"
    ]

    bootstrap.build_pipeline().execute(
        PipelineContext(
            message=message,
        )
    )

    store = bootstrap.build_message_store()

    ids = store.list_messages(
        "bob@receiver.onion"
    )

    assert len(ids) == 1
    assert bootstrap.build_queue().size() == 0

    stored = store.get(
        "bob@receiver.onion",
        ids[0],
    )

    assert stored is not None
    assert stored.body == message.body

    store.backend.close()