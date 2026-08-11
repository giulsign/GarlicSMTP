from garlicsmtp.application.view_model import (
    ApplicationViewModel,
)
from garlicsmtp.core.engine.state import (
    RuntimeState,
)
from tests.support import (
    make_application_status,
)
from garlicsmtp.application import (
    ApplicationEventLevel,
    ApplicationEventLog,
    ApplicationEventSource,
    MessageListViewModel,
)

class FakeMessageExplorer:

    def list_messages(
        self,
        mailbox,
    ):
        del mailbox
        return ()

class FakeApplicationController:

    def __init__(self):
        self.current_status = make_application_status()
        self.start_calls = 0
        self.stop_calls = 0
        self.restart_calls = 0

    def status(self):
        return self.current_status

    def start(self):
        self.start_calls += 1

        self.current_status = make_application_status(
            runtime_state=(
                RuntimeState.RUNNING
            ),
            smtp_running=True,
            imap_running=True,
            queue_worker_running=True,
        )

        return self.current_status

    def stop(self):
        self.stop_calls += 1
        self.current_status = make_application_status()

        return self.current_status

    def restart(self):
        self.restart_calls += 1

        self.current_status = make_application_status(
            runtime_state=(
                RuntimeState.RUNNING
            ),
            smtp_running=True,
            imap_running=True,
            queue_worker_running=True,
        )

        return self.current_status

def test_application_view_model_reports_stopped_state():
    controller = FakeApplicationController()

    view_model = ApplicationViewModel(
        controller
    )

    assert view_model.application_name == (
        "GarlicSMTP"
    )

    assert view_model.hostname == (
        "garlicsmtp.local"
    )

    assert view_model.local_domain == (
        "test.onion"
    )

    assert view_model.runtime_text == (
        "Stopped"
    )

    assert view_model.runtime_status_key == (
        "stopped"
    )

    assert view_model.is_running is False
    assert view_model.can_start is True
    assert view_model.can_stop is False
    assert view_model.can_restart is False

def test_application_view_model_formats_services():
    controller = FakeApplicationController()

    view_model = ApplicationViewModel(
        controller
    )

    assert view_model.smtp.name == (
        "SMTP Server"
    )

    assert view_model.smtp.status_text == (
        "Stopped"
    )

    assert view_model.smtp.status_key == (
        "stopped"
    )

    assert view_model.imap.name == (
        "IMAP Server"
    )

    assert view_model.queue_worker.name == (
        "Queue Worker"
    )

def test_application_view_model_formats_counts():
    controller = FakeApplicationController()

    controller.current_status = make_application_status(
        smtp_connections=1,
        imap_connections=3,
        pending_messages=2,
        mailboxes=(
            "inbox@test.onion",
            "archive@test.onion",
        ),
    )

    view_model = ApplicationViewModel(
        controller
    )

    assert (
        view_model.smtp_connections_text
        == "1 connection"
    )

    assert (
        view_model.imap_connections_text
        == "3 connections"
    )

    assert (
        view_model.pending_messages_text
        == "2 messages queued"
    )

    assert (
        view_model.mailbox_count_text
        == "2 mailboxes"
    )

    assert view_model.mailbox_names == (
        "inbox@test.onion",
        "archive@test.onion",
    )

    assert view_model.mailbox_names_text == (
        "inbox@test.onion, "
        "archive@test.onion"
    )

def test_application_view_model_formats_empty_mailboxes():
    view_model = ApplicationViewModel(
        FakeApplicationController()
    )

    assert view_model.mailbox_names == ()
    assert view_model.mailbox_names_text == (
        "No mailboxes"
    )

    assert view_model.mailbox_count_text == (
        "0 mailboxes"
    )

def test_application_view_model_starts_application():
    controller = FakeApplicationController()

    view_model = ApplicationViewModel(
        controller
    )

    view_model.start()

    assert controller.start_calls == 1
    assert view_model.is_running is True
    assert view_model.runtime_text == (
        "Running"
    )

    assert view_model.can_start is False
    assert view_model.can_stop is True
    assert view_model.can_restart is True

    assert view_model.smtp.running is True
    assert view_model.imap.running is True

    assert (
        view_model.queue_worker.running
        is True
    )

def test_application_view_model_stops_application():
    controller = FakeApplicationController()

    view_model = ApplicationViewModel(
        controller
    )

    view_model.start()
    view_model.stop()

    assert controller.stop_calls == 1
    assert view_model.is_running is False
    assert view_model.runtime_text == (
        "Stopped"
    )

def test_application_view_model_restarts_application():
    controller = FakeApplicationController()

    view_model = ApplicationViewModel(
        controller
    )

    view_model.restart()

    assert controller.restart_calls == 1
    assert view_model.is_running is True

def test_application_view_model_refreshes_status():
    controller = FakeApplicationController()

    view_model = ApplicationViewModel(
        controller
    )

    controller.current_status = make_application_status(
        pending_messages=4,
        mailboxes=(
            "bob@test.onion",
        ),
    )

    view_model.refresh()

    assert (
        view_model.pending_messages_text
        == "4 messages queued"
    )

    assert view_model.mailbox_names == (
        "bob@test.onion",
    )


def test_application_view_model_formats_endpoints():
    view_model = ApplicationViewModel(
        FakeApplicationController()
    )

    assert (
        view_model.smtp_endpoint_text
        == "127.0.0.1:2525"
    )

    assert (
        view_model.imap_endpoint_text
        == "127.0.0.1:1143"
    )


def test_application_view_model_formats_activity():
    controller = (
        FakeApplicationController()
    )

    controller.context = type(
        "Context",
        (),
        {
            "event_log": (
                ApplicationEventLog()
            )
        },
    )()

    controller.context.event_log.record(
        source=(
            ApplicationEventSource.TOR
        ),
        level=(
            ApplicationEventLevel.INFO
        ),
        message="Tor became ready",
    )

    view_model = ApplicationViewModel(
        controller
    )

    entries = (
        view_model.activity_entries
    )

    assert len(entries) == 1
    assert entries[0].source_text == "Tor"
    assert entries[0].short_text == (
        "Tor became ready"
    )


def test_application_view_model_clears_activity():
    controller = (
        FakeApplicationController()
    )

    controller.context = type(
        "Context",
        (),
        {
            "event_log": (
                ApplicationEventLog()
            )
        },
    )()

    controller.context.event_log.record(
        source=(
            ApplicationEventSource.TOR
        ),
        level=(
            ApplicationEventLevel.INFO
        ),
        message="Tor became ready",
    )

    view_model = ApplicationViewModel(
        controller
    )

    notifications = []

    view_model.subscribe(
        lambda: notifications.append(
            "changed"
        )
    )

    view_model.clear_activity()

    assert view_model.events == ()
    assert notifications == [
        "changed",
    ]


def test_application_view_model_exposes_message_list():
    message_list = MessageListViewModel(
        FakeMessageExplorer()
    )

    view_model = ApplicationViewModel(
        FakeApplicationController(),
        message_list=message_list,
    )

    assert view_model.message_list is (
        message_list
    )