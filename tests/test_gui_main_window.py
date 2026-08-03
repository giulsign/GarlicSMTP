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

    window.refresh_timer.stop()

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

    window.refresh_timer.stop()

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
