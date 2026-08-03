from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from garlicsmtp.application import (
    ApplicationViewModel,
)


class MainWindow(QMainWindow):

    def __init__(
        self,
        view_model: ApplicationViewModel,
    ) -> None:
        super().__init__()

        self.view_model = view_model

        self.setWindowTitle(
            "GarlicSMTP"
        )

        self.resize(
            620,
            560,
        )

        self._build_ui()
        self._connect_actions()
        self.refresh_view()

        self.refresh_timer = QTimer(
            self
        )

        self.refresh_timer.setInterval(
            1000
        )

        self.refresh_timer.timeout.connect(
            self.refresh
        )

        self.refresh_timer.start()

    def _build_ui(
        self,
    ) -> None:
        central_widget = QWidget(
            self
        )

        root_layout = QVBoxLayout(
            central_widget
        )

        root_layout.addWidget(
            self._build_runtime_group()
        )

        root_layout.addWidget(
            self._build_identity_group()
        )

        root_layout.addWidget(
            self._build_activity_group()
        )

        root_layout.addWidget(
            self._build_mailbox_group()
        )

        root_layout.addLayout(
            self._build_action_layout()
        )

        self.setCentralWidget(
            central_widget
        )

    def _build_runtime_group(
        self,
    ) -> QGroupBox:
        group = QGroupBox(
            "Services"
        )

        layout = QFormLayout(
            group
        )

        self.runtime_value = QLabel()
        self.smtp_value = QLabel()
        self.imap_value = QLabel()
        self.worker_value = QLabel()

        layout.addRow(
            "Runtime:",
            self.runtime_value,
        )

        layout.addRow(
            "SMTP Server:",
            self.smtp_value,
        )

        layout.addRow(
            "IMAP Server:",
            self.imap_value,
        )

        layout.addRow(
            "Queue Worker:",
            self.worker_value,
        )

        return group

    def _build_identity_group(
        self,
    ) -> QGroupBox:
        group = QGroupBox(
            "Identity"
        )

        layout = QFormLayout(
            group
        )

        self.hostname_value = QLabel()
        self.domain_value = QLabel()

        layout.addRow(
            "Hostname:",
            self.hostname_value,
        )

        layout.addRow(
            "Local domain:",
            self.domain_value,
        )

        return group

    def _build_activity_group(
        self,
    ) -> QGroupBox:
        group = QGroupBox(
            "Activity"
        )

        layout = QFormLayout(
            group
        )

        self.queue_value = QLabel()
        self.mailbox_count_value = QLabel()
        self.smtp_connections_value = QLabel()
        self.imap_connections_value = QLabel()

        layout.addRow(
            "Queue:",
            self.queue_value,
        )

        layout.addRow(
            "Mailboxes:",
            self.mailbox_count_value,
        )

        layout.addRow(
            "SMTP connections:",
            self.smtp_connections_value,
        )

        layout.addRow(
            "IMAP connections:",
            self.imap_connections_value,
        )

        return group

    def _build_mailbox_group(
        self,
    ) -> QGroupBox:
        group = QGroupBox(
            "Mailbox list"
        )

        layout = QVBoxLayout(
            group
        )

        self.mailbox_list = QListWidget()

        layout.addWidget(
            self.mailbox_list
        )

        return group

    def _build_action_layout(
        self,
    ) -> QHBoxLayout:
        layout = QHBoxLayout()

        self.start_button = QPushButton(
            "Start"
        )

        self.stop_button = QPushButton(
            "Stop"
        )

        self.restart_button = QPushButton(
            "Restart"
        )

        self.refresh_button = QPushButton(
            "Refresh"
        )

        layout.addWidget(
            self.start_button
        )

        layout.addWidget(
            self.stop_button
        )

        layout.addWidget(
            self.restart_button
        )

        layout.addStretch()

        layout.addWidget(
            self.refresh_button
        )

        return layout

    def _connect_actions(
        self,
    ) -> None:
        self.start_button.clicked.connect(
            self.start
        )

        self.stop_button.clicked.connect(
            self.stop
        )

        self.restart_button.clicked.connect(
            self.restart
        )

        self.refresh_button.clicked.connect(
            self.refresh
        )

    def start(
        self,
    ) -> None:
        self._execute_action(
            self.view_model.start
        )

    def stop(
        self,
    ) -> None:
        self._execute_action(
            self.view_model.stop
        )

    def restart(
        self,
    ) -> None:
        self._execute_action(
            self.view_model.restart
        )

    def refresh(
        self,
    ) -> None:
        self._execute_action(
            self.view_model.refresh
        )

    def _execute_action(
        self,
        action,
    ) -> None:
        try:
            action()

        except Exception as exc:
            QMessageBox.critical(
                self,
                "GarlicSMTP error",
                str(exc),
            )

        self.refresh_view()

    def refresh_view(
        self,
    ) -> None:
        self.runtime_value.setText(
            self.view_model.runtime_text
        )

        self.smtp_value.setText(
            self.view_model.smtp.status_text
        )

        self.imap_value.setText(
            self.view_model.imap.status_text
        )

        self.worker_value.setText(
            self.view_model
            .queue_worker
            .status_text
        )

        self.hostname_value.setText(
            self.view_model.hostname
        )

        self.domain_value.setText(
            self.view_model.local_domain
        )

        self.queue_value.setText(
            self.view_model
            .pending_messages_text
        )

        self.mailbox_count_value.setText(
            self.view_model
            .mailbox_count_text
        )

        self.smtp_connections_value.setText(
            self.view_model
            .smtp_connections_text
        )

        self.imap_connections_value.setText(
            self.view_model
            .imap_connections_text
        )

        self.mailbox_list.clear()

        self.mailbox_list.addItems(
            list(
                self.view_model.mailbox_names
            )
        )

        self.start_button.setEnabled(
            self.view_model.can_start
        )

        self.stop_button.setEnabled(
            self.view_model.can_stop
        )

        self.restart_button.setEnabled(
            self.view_model.can_restart
        )

    def closeEvent(
        self,
        event,
    ) -> None:
        self.refresh_timer.stop()

        if self.view_model.is_running:
            self.view_model.stop()

        event.accept()
