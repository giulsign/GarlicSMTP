from garlicsmtp.application import (
    ApplicationBuilder,
    ApplicationStatusProvider,
)
from garlicsmtp.configuration import (
    ApplicationPaths,
    ApplicationSettings,
)
from garlicsmtp.core.engine.state import (
    RuntimeState,
)
from garlicsmtp.queue.factory import (
    QueueFactory,
)



def test_application_status_reports_stopped_state(
    tmp_path,
):
    context = ApplicationBuilder(
        paths=ApplicationPaths(
            root_dir=tmp_path / "garlicsmtp"
        ),
        settings=ApplicationSettings(),
    ).build()

    status = ApplicationStatusProvider(
        context
    ).snapshot()

    assert (
        status.runtime_state
        is RuntimeState.STOPPED
    )

    assert status.running is False

    assert status.smtp_running is False
    assert status.imap_running is False

    assert (
        status.queue_worker_running
        is False
    )

    assert status.smtp_connections == 0
    assert status.imap_connections == 0

    assert status.pending_messages == 0
    assert status.mailboxes == ()
    assert status.mailbox_count == 0

    assert status.hostname == (
        "garlicsmtp.local"
    )

    assert status.local_domain == (
        "test.onion"
    )

    context.queue.backend.close()
    context.store.backend.close()


def test_application_status_reports_data(
    tmp_path,
    message,
):
    context = ApplicationBuilder(
        paths=ApplicationPaths(
            root_dir=tmp_path / "garlicsmtp"
        ),
        settings=ApplicationSettings(),
    ).build()

    context.store.create_mailbox(
        "bob@test.onion"
    )

    context.queue.enqueue(
        QueueFactory.create(
            message
        )
    )

    status = ApplicationStatusProvider(
        context
    ).snapshot()

    assert status.pending_messages == 1

    assert status.mailboxes == (
        "bob@test.onion",
    )

    assert status.mailbox_count == 1

    context.queue.backend.close()
    context.store.backend.close()


def test_application_status_is_a_fresh_snapshot(
    tmp_path,
):
    context = ApplicationBuilder(
        paths=ApplicationPaths(
            root_dir=tmp_path / "garlicsmtp"
        ),
        settings=ApplicationSettings(),
    ).build()

    provider = ApplicationStatusProvider(
        context
    )

    before = provider.snapshot()

    context.store.create_mailbox(
        "archive@test.onion"
    )

    after = provider.snapshot()

    assert before.mailbox_count == 0
    assert after.mailbox_count == 1

    context.queue.backend.close()
    context.store.backend.close()


def test_status_provider_builds_mailbox_summaries(
    context,
    message,
):
    mailbox = "alice@test.onion"

    message.envelope.recipients = [
        mailbox
    ]

    context.store.store(
        mailbox,
        message,
    )

    status = (
        ApplicationStatusProvider(
            context
        )
        .snapshot()
    )

    assert len(
        status.mailbox_summaries
    ) == 1

    summary = (
        status.mailbox_summaries[0]
    )

    assert summary.address == mailbox
    assert summary.message_count == 1