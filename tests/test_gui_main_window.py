import os

os.environ.setdefault(
    "QT_QPA_PLATFORM",
    "offscreen",
)
from garlicsmtp.models import (
    Envelope,
    MailHeaders,
    MailMessage,
    Metadata,
)
from PySide6.QtWidgets import (
    QApplication,
)
from garlicsmtp.storage.entry import (
    MessageEntry,
)
from garlicsmtp.application.view_model import (
    ApplicationViewModel,
)
from garlicsmtp.core.engine.state import (
    RuntimeState,
)
from garlicsmtp.gui.main_window import (
    MainWindow,
)
from tests.support import (
    make_application_status,
)
from tests.support import (
    make_application_status,
    make_tor_status,
)
from garlicsmtp.application import (
    ApplicationEventLevel,
    ApplicationEventLog,
    ApplicationEventSource,
)
from datetime import UTC, datetime

from garlicsmtp.application import (
    MessageListViewModel,
    MessageSummary,
    MessagePreviewViewModel,
)
from PySide6.QtWidgets import (
    QApplication,
    QMessageBox,
)
from garlicsmtp.application.compose_view_model import (
    ComposeViewModel,
)

class FakePreviewExplorer:

    def __init__(
        self,
    ):
        self.deleted = set()

    def list_messages(
        self,
        mailbox,
    ):
        if mailbox != "bob@test.onion":
            return ()

        if "message-1" in self.deleted:
            return ()

        return (
            MessageSummary(
                id="message-1",
                uid=1,
                sender="alice@test.onion",
                subject="Preview integration",
                internal_date=datetime(
                    2026,
                    8,
                    7,
                    9,
                    30,
                    tzinfo=UTC,
                ),
                size=128,
                flags=(),
            ),
        )

    def get_message(
        self,
        mailbox,
        message_id,
    ):
        if (
            mailbox != "bob@test.onion"
            or message_id != "message-1"
        ):
            return None

        if message_id in self.deleted:
            return None

        headers = MailHeaders()

        headers.add(
            "Subject",
            "Preview integration",
        )

        return MessageEntry(
            id="message-1",
            mailbox=mailbox,
            uid=1,
            message=MailMessage(
                envelope=Envelope(
                    sender="alice@test.onion",
                    recipients=[
                        "bob@test.onion",
                    ],
                ),
                headers=headers,
                metadata=Metadata(),
                body="Preview body",
            ),
            internal_date=datetime(
                2026,
                8,
                7,
                9,
                30,
                tzinfo=UTC,
            ),
            flags=set(),
        )

    def delete_message(
        self,
        mailbox,
        message_id,
    ):
        if (
            mailbox != "bob@test.onion"
            or message_id != "message-1"
        ):
            return False

        self.deleted.add(
            message_id
        )

        return True


class FakeMessageExplorer:

    def list_messages(
        self,
        mailbox,
    ):
        if mailbox != "bob@test.onion":
            return ()

        return (
            MessageSummary(
                id="message-1",
                uid=1,
                sender="alice@test.onion",
                subject="GarlicSMTP message",
                internal_date=datetime(
                    2026,
                    8,
                    6,
                    10,
                    30,
                    tzinfo=UTC,
                ),
                size=128,
                flags=(),
            ),
        )

class FakeController:

    def __init__(self):
        self.current_status = (
            self._stopped_status()
        )

    @staticmethod
    def _stopped_status():
        return make_application_status(
            pending_messages=2,
            mailboxes=(
                "bob@test.onion",
                "archive@test.onion",
            ),
        )

    @staticmethod
    def _running_status():
        return make_application_status(
            runtime_state=(
                RuntimeState.RUNNING
            ),
            smtp_running=True,
            imap_running=True,
            queue_worker_running=True,
            smtp_connections=1,
            imap_connections=2,
            pending_messages=2,
            mailboxes=(
                "bob@test.onion",
                "archive@test.onion",
            ),
        )

    def status(self):
        return self.current_status

    def start(self):
        self.current_status = (
            self._running_status()
        )

        return self.current_status

    def stop(self):
        self.current_status = (
            self._stopped_status()
        )

        return self.current_status

    def restart(self):
        self.current_status = (
            self._running_status()
        )

        return self.current_status


def get_application():
    return (
        QApplication.instance()
        or QApplication([])
    )


def test_main_window_displays_status():
    get_application()

    view_model = ApplicationViewModel(
        FakeController()
    )

    window = MainWindow(
        view_model
    )

    assert window.runtime_value.text() == (
        "Stopped"
    )

    assert window.smtp_value.text() == (
        "Stopped"
    )

    assert window.hostname_value.text() == (
        "garlicsmtp.local"
    )

    assert window.queue_value.text() == (
        "2 messages queued"
    )

    assert window.mailbox_list.count() == 2

    assert window.start_button.isEnabled()
    assert not window.stop_button.isEnabled()

    window.close()


def test_main_window_starts_application():
    get_application()

    view_model = ApplicationViewModel(
        FakeController()
    )

    window = MainWindow(
        view_model
    )

    window.start()

    assert window.runtime_value.text() == (
        "Running"
    )

    assert window.smtp_value.text() == (
        "Running"
    )

    assert not window.start_button.isEnabled()
    assert window.stop_button.isEnabled()

    window.stop()
    window.close()


def test_main_window_displays_tor_status():
    get_application()

    controller = FakeController()

    controller.current_status = (
        make_application_status(
            tor=make_tor_status(
                control_enabled=True,
                control_available=True,
                authenticated=True,
                authentication_method=(
                    "SAFECOOKIE"
                ),
                socks_available=True,
                version="0.4.8.12",
                bootstrap_progress=100,
                bootstrap_summary="Done",
                built_circuits=3,
                active_streams=1,
                last_error=None,
                socks_listeners=(
                    "127.0.0.1:9050",
                ),
                control_listeners=(
                    "127.0.0.1:9051",
                ),
            )
        )
    )

    view_model = ApplicationViewModel(
        controller
    )

    window = MainWindow(
        view_model
    )

    assert (
        window.tor_status_value.text()
        == "Ready"
    )

    assert (
        window.tor_socks_value.text()
        == "127.0.0.1:9050"
    )

    assert (
        window.tor_control_value.text()
        == "127.0.0.1:9051"
    )

    assert (
        window.tor_version_value.text()
        == "0.4.8.12"
    )

    assert (
        window.tor_bootstrap_value.text()
        == "100% — Done"
    )

    assert (
        window.tor_circuits_value.text()
        == "3 built circuits"
    )

    assert (
        window.tor_streams_value.text()
        == "1 active stream"
    )

    window.close()


def test_main_window_displays_activity():
    get_application()

    controller = FakeController()

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

    window = MainWindow(
        ApplicationViewModel(
            controller
        )
    )

    assert (
        window.activity_list.count()
        == 1
    )

    assert "Tor became ready" in (
        window.activity_list
        .item(0)
        .text()
    )

    window.close()


def test_main_window_builds_dashboard_sections():
    get_application()

    window = MainWindow(
        ApplicationViewModel(
            FakeController()
        )
    )

    assert (
        window.application_section
        is not None
    )

    assert (
        window.services_section
        is not None
    )

    assert (
        window.tor_section
        is not None
    )

    assert (
        window.activity_section
        is not None
    )

    window.close()


def test_main_window_refreshes_all_sections():
    get_application()

    window = MainWindow(
        ApplicationViewModel(
            FakeController()
        )
    )

    calls = []

    window.application_section.refresh_view = (
        lambda: calls.append(
            "application"
        )
    )

    window.services_section.refresh_view = (
        lambda: calls.append(
            "services"
        )
    )

    window.tor_section.refresh_view = (
        lambda: calls.append(
            "tor"
        )
    )

    window.activity_section.refresh_view = (
        lambda: calls.append(
            "activity"
        )
    )

    window.refresh_view()

    assert calls == [
        "application",
        "services",
        "tor",
        "activity",
    ]

    window.close()


def test_main_window_loads_selected_mailbox_messages():
    get_application()

    controller = FakeController()

    message_list = MessageListViewModel(
        FakeMessageExplorer()
    )

    view_model = ApplicationViewModel(
        controller,
        message_list=message_list,
    )

    window = MainWindow(
        view_model
    )

    assert window.mailbox_section.select_mailbox(
        "bob@test.onion"
    ) is True

    assert (
        window.message_list_section
        .table
        .rowCount()
        == 1
    )

    assert (
        window.message_list_section
        .table
        .item(
            0,
            window.message_list_section
            .COLUMN_SUBJECT,
        )
        .text()
        == "GarlicSMTP message"
    )

    assert (
        view_model.message_list
        .selected_mailbox
        == "bob@test.onion"
    )

    window.close()


def test_main_window_displays_selected_message_preview():
    get_application()

    controller = FakeController()
    explorer = FakePreviewExplorer()

    message_list = MessageListViewModel(
        explorer
    )

    message_preview = MessagePreviewViewModel(
        explorer
    )

    view_model = ApplicationViewModel(
        controller,
        message_list=message_list,
        message_preview=message_preview,
    )

    window = MainWindow(
        view_model
    )

    assert window.mailbox_section.select_mailbox(
        "bob@test.onion"
    ) is True

    assert window.message_list_section.select_message(
        "message-1"
    ) is True

    assert (
        window.message_preview_section
        .subject_value
        .text()
        == "Preview integration"
    )

    assert (
        window.message_preview_section
        .body_value
        .toPlainText()
        == "Preview body"
    )

    window.close()


def test_main_window_refreshes_message_explorer_sections():
    get_application()

    window = MainWindow(
        ApplicationViewModel(
            FakeController()
        )
    )

    calls = []

    window.message_list_section.refresh_view = (
        lambda: calls.append(
            "message_list"
        )
    )

    window.message_preview_section.refresh_view = (
        lambda: calls.append(
            "message_preview"
        )
    )

    window.refresh_view()

    assert "message_list" in calls
    assert "message_preview" in calls

    window.close()

def test_main_window_clears_preview_after_message_delete(
    monkeypatch,
):
    get_application()

    controller = FakeController()
    explorer = FakePreviewExplorer()

    message_list = MessageListViewModel(
        explorer
    )

    message_preview = MessagePreviewViewModel(
        explorer
    )

    view_model = ApplicationViewModel(
        controller,
        message_list=message_list,
        message_preview=message_preview,
    )

    window = MainWindow(
        view_model
    )

    assert window.mailbox_section.select_mailbox(
        "bob@test.onion"
    ) is True

    assert window.message_list_section.select_message(
        "message-1"
    ) is True

    assert (
        window.message_preview_section
        .subject_value
        .text()
        == "Preview integration"
    )

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: (
            QMessageBox.StandardButton.Yes
        ),
    )

    window.message_list_section.delete_button.click()

    assert (
        window.message_list_section
        .table
        .rowCount()
        == 0
    )

    assert (
        view_model.message_list
        .selected_message_id
        is None
    )

    assert (
        view_model.message_preview
        .message_id
        is None
    )

    assert (
        window.message_preview_section
        .placeholder_value
        .text()
        == "Select a message"
    )

    assert (
        window.message_preview_section
        .details_widget
        .isHidden()
        is True
    )

    window.close()


def test_main_window_places_message_list_and_preview_side_by_side():
    get_application()

    window = MainWindow(
        ApplicationViewModel(
            FakeController()
        )
    )

    list_index = (
        window.dashboard_layout.indexOf(
            window.message_list_section
        )
    )

    preview_index = (
        window.dashboard_layout.indexOf(
            window.message_preview_section
        )
    )

    (
        list_row,
        list_column,
        list_row_span,
        list_column_span,
    ) = window.dashboard_layout.getItemPosition(
        list_index
    )

    (
        preview_row,
        preview_column,
        preview_row_span,
        preview_column_span,
    ) = window.dashboard_layout.getItemPosition(
        preview_index
    )

    assert (
        list_row,
        list_column,
        list_row_span,
        list_column_span,
    ) == (
        4,
        0,
        1,
        1,
    )

    assert (
        preview_row,
        preview_column,
        preview_row_span,
        preview_column_span,
    ) == (
        4,
        1,
        1,
        1,
    )

    window.close()


def test_main_window_builds_compose_section():
    get_application()

    class FakeComposer:
        def send(
            self,
            *,
            sender,
            recipient,
            subject,
            body,
        ):
            del sender
            del recipient
            del subject
            del body
            return True

    compose = ComposeViewModel(
        FakeComposer()
    )

    window = MainWindow(
        ApplicationViewModel(
            FakeController(),
            compose=compose,
        )
    )

    assert window.compose_section is not None

    window.close()


def test_main_window_refreshes_compose_section():
    get_application()

    class FakeComposer:
        def send(
            self,
            *,
            sender,
            recipient,
            subject,
            body,
        ):
            return True

    compose = ComposeViewModel(
        FakeComposer()
    )

    window = MainWindow(
        ApplicationViewModel(
            FakeController(),
            compose=compose,
        )
    )

    calls = []

    window.compose_section.refresh_view = (
        lambda: calls.append(
            "compose"
        )
    )

    window.refresh_view()

    assert "compose" in calls

    window.close()