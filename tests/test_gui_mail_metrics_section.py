from garlicsmtp.application import (
    ApplicationViewModel,
)
from garlicsmtp.gui.sections import (
    MailMetricsSection,
)
from tests.support import (
    make_application_status,
)
from tests.test_gui_main_window import (
    FakeController,
    get_application,
)


def test_mail_metrics_section_displays_metrics():
    get_application()

    controller = FakeController()

    controller.current_status = (
        make_application_status(
            pending_messages=7,
            smtp_connections=2,
            imap_connections=3,
            mailboxes=(
                "alice@test.onion",
                "bob@test.onion",
            ),
        )
    )

    section = MailMetricsSection(   
        view_model=ApplicationViewModel(
            controller
        )
    )

    section.refresh_view()

    assert (
        section.queue_value.text()
        == "7 messages queued"
    )

    assert (
        section.mailbox_count_value.text()
        == "2 mailboxes"
    )

    assert (
        section.smtp_connections_value.text()
        == "2 connections"
    )

    assert (
        section.imap_connections_value.text()
        == "3 connections"
    )

    section.close()
