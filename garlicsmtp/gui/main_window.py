from collections.abc import Callable

from PySide6.QtCore import (
    QObject,
    Signal,
)
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from garlicsmtp.application import (
    ApplicationViewModel,
)
from garlicsmtp.gui.dashboard_widgets import (
    DashboardCard,
    MetricValue,
    StatusBadge,
)
from garlicsmtp.gui.sections import (
    ActivitySection,
    ApplicationSection,
    ServicesSection,
    TorSection,
)


class ViewModelEventBridge(QObject):

    refresh_requested = Signal()

    def request_refresh(
        self,
    ) -> None:
        self.refresh_requested.emit()


class MainWindow(QMainWindow):

    def __init__(
        self,
        view_model: ApplicationViewModel,
    ) -> None:
        super().__init__()

        self.view_model = view_model

        self.setWindowTitle(
            "GarlicSMTP Monitor"
        )

        self.resize(
            980,
            720,
        )

        self.event_bridge = (
            ViewModelEventBridge()
        )

        self.event_bridge.refresh_requested.connect(
            self.refresh_view
        )

        self.view_model.subscribe(
            self.event_bridge.request_refresh
        )

        self._build_ui()
        self._connect_actions()
        self.refresh_view()

    def _build_ui(
        self,
    ) -> None:
        central_widget = QWidget(
            self
        )

        root_layout = QVBoxLayout(
            central_widget
        )

        root_layout.setContentsMargins(
            18,
            18,
            18,
            18,
        )

        root_layout.setSpacing(
            14
        )

        root_layout.addWidget(
            self._build_header()
        )

        scroll_area = QScrollArea(
            self
        )

        scroll_area.setWidgetResizable(
            True
        )

        scroll_content = QWidget()

        self.dashboard_layout = QGridLayout(
            scroll_content
        )

        self.dashboard_layout.setSpacing(
            14
        )

        self._build_dashboard_sections()
        self._add_dashboard_sections()

        self.dashboard_layout.addWidget(
            self._build_mail_card(),
            3,
            0,
        )

        self.dashboard_layout.addWidget(
            self._build_mailbox_card(),
            3,
            1,
        )

        self.dashboard_layout.setColumnStretch(
            0,
            1,
        )

        self.dashboard_layout.setColumnStretch(
            1,
            1,
        )

        scroll_area.setWidget(
            scroll_content
        )

        root_layout.addWidget(
            scroll_area
        )

        root_layout.addLayout(
            self._build_action_layout()
        )

        self.setCentralWidget(
            central_widget
        )

    def _build_dashboard_sections(
        self,
    ) -> None:
        self.application_section = (
            ApplicationSection(
                view_model=self.view_model,
            )
        )

        self.services_section = (
            ServicesSection(
                view_model=self.view_model,
            )
        )

        self.tor_section = TorSection(
            view_model=self.view_model,
        )

        self.activity_section = (
            ActivitySection(
                view_model=self.view_model,
            )
        )

        self._install_compatibility_aliases()

    def _add_dashboard_sections(
        self,
    ) -> None:
        self.dashboard_layout.addWidget(
            self.application_section,
            0,
            0,
        )

        self.dashboard_layout.addWidget(
            self.services_section,
            0,
            1,
        )

        self.dashboard_layout.addWidget(
            self.tor_section,
            1,
            0,
            1,
            2,
        )

        self.dashboard_layout.addWidget(
            self.activity_section,
            2,
            0,
            1,
            2,
        )

    def _install_compatibility_aliases(
        self,
    ) -> None:
        self.runtime_value = (
            self.application_section
            .runtime_value
        )

        self.hostname_value = (
            self.application_section
            .hostname_value
        )

        self.domain_value = (
            self.application_section
            .domain_value
        )

        self.smtp_value = (
            self.services_section
            .smtp_value
        )

        self.imap_value = (
            self.services_section
            .imap_value
        )

        self.worker_value = (
            self.services_section
            .worker_value
        )

        self.smtp_endpoint_value = (
            self.services_section
            .smtp_endpoint_value
        )

        self.imap_endpoint_value = (
            self.services_section
            .imap_endpoint_value
        )

        self.tor_status_value = (
            self.tor_section
            .status_value
        )

        self.tor_socks_value = (
            self.tor_section
            .socks_value
        )

        self.tor_control_value = (
            self.tor_section
            .control_value
        )

        self.tor_version_value = (
            self.tor_section
            .version_value
        )

        self.tor_bootstrap_value = (
            self.tor_section
            .bootstrap_value
        )

        self.tor_circuits_value = (
            self.tor_section
            .circuits_value
        )

        self.tor_streams_value = (
            self.tor_section
            .streams_value
        )

        self.tor_onion_smtp_value = (
            self.tor_section
            .onion_smtp_value
        )

        self.tor_error_value = (
            self.tor_section
            .error_value
        )

        self.activity_list = (
            self.activity_section
            .activity_list
        )

        self.activity_clear_button = (
            self.activity_section
            .clear_button
        )

    def _build_header(
        self,
    ) -> QWidget:
        widget = QWidget()

        layout = QHBoxLayout(
            widget
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        title = QLabel(
            "GarlicSMTP"
        )

        title.setStyleSheet(
            """
            QLabel {
                font-size: 26px;
                font-weight: 700;
            }
            """
        )

        subtitle = QLabel(
            "Private mail infrastructure monitor"
        )

        subtitle.setStyleSheet(
            """
            QLabel {
                color: #777777;
                font-size: 12px;
            }
            """
        )

        title_layout = QVBoxLayout()

        title_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        title_layout.addWidget(
            title
        )

        title_layout.addWidget(
            subtitle
        )

        self.runtime_badge = StatusBadge()

        layout.addLayout(
            title_layout
        )

        layout.addStretch()

        layout.addWidget(
            self.runtime_badge
        )

        return widget

    def _build_mail_card(
        self,
    ) -> DashboardCard:
        card = DashboardCard(
            "Mail activity"
        )

        self.queue_metric = MetricValue(
            "Queue"
        )

        self.mailbox_metric = MetricValue(
            "Mailboxes"
        )

        self.smtp_connections_metric = (
            MetricValue(
                "SMTP connections"
            )
        )

        self.imap_connections_metric = (
            MetricValue(
                "IMAP connections"
            )
        )

        # Alias temporanei per i test esistenti.
        self.queue_value = (
            self.queue_metric.value_label
        )

        self.mailbox_count_value = (
            self.mailbox_metric.value_label
        )

        self.smtp_connections_value = (
            self.smtp_connections_metric
            .value_label
        )

        self.imap_connections_value = (
            self.imap_connections_metric
            .value_label
        )

        metrics = QWidget()

        layout = QGridLayout(
            metrics
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        layout.addWidget(
            self.queue_metric,
            0,
            0,
        )

        layout.addWidget(
            self.mailbox_metric,
            0,
            1,
        )

        layout.addWidget(
            self.smtp_connections_metric,
            1,
            0,
        )

        layout.addWidget(
            self.imap_connections_metric,
            1,
            1,
        )

        card.add_widget(
            metrics
        )

        return card

    def _build_mailbox_card(
        self,
    ) -> DashboardCard:
        card = DashboardCard(
            "Mailboxes"
        )

        self.mailbox_list = QListWidget()

        self.mailbox_list.setMinimumHeight(
            160
        )

        card.add_widget(
            self.mailbox_list
        )

        return card

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
        action: Callable[[], object],
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

    def _refresh_sections(
        self,
    ) -> None:
        sections = (
            self.application_section,
            self.services_section,
            self.tor_section,
            self.activity_section,
        )

        for section in sections:
            section.refresh_view()

    def refresh_view(
        self,
    ) -> None:
        self._refresh_sections()

        self.runtime_badge.set_status(
            text=self.view_model.runtime_text,
            status_key=(
                self.view_model
                .runtime_status_key
            ),
        )

        self.queue_metric.setText(
            self.view_model
            .pending_messages_text
        )

        self.mailbox_metric.setText(
            self.view_model
            .mailbox_count_text
        )

        self.smtp_connections_metric.setText(
            self.view_model
            .smtp_connections_text
        )

        self.imap_connections_metric.setText(
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
        self.view_model.unsubscribe(
            self.event_bridge.request_refresh
        )

        if self.view_model.is_running:
            self.view_model.stop()

        self.view_model.close()

        event.accept()
