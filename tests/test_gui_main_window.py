import os

os.environ.setdefault(
    "QT_QPA_PLATFORM",
    "offscreen",
)

from PySide6.QtWidgets import (
    QApplication,
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