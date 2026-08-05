from PySide6.QtWidgets import (
    QGridLayout,
    QWidget,
)

from garlicsmtp.application import (
    ApplicationViewModel,
)
from garlicsmtp.gui.dashboard_widgets import (
    DashboardCard,
    MetricValue,
)


class MailMetricsSection(DashboardCard):

    def __init__(
        self,
        *,
        view_model: ApplicationViewModel,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            "Mail activity",
            parent=parent,
        )

        self.view_model = view_model

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

        metrics_widget = QWidget(
            self
        )

        metrics_layout = QGridLayout(
            metrics_widget
        )

        metrics_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        metrics_layout.setHorizontalSpacing(
            18
        )

        metrics_layout.setVerticalSpacing(
            14
        )

        metrics_layout.addWidget(
            self.queue_metric,
            0,
            0,
        )

        metrics_layout.addWidget(
            self.mailbox_metric,
            0,
            1,
        )

        metrics_layout.addWidget(
            self.smtp_connections_metric,
            1,
            0,
        )

        metrics_layout.addWidget(
            self.imap_connections_metric,
            1,
            1,
        )

        metrics_layout.setColumnStretch(
            0,
            1,
        )

        metrics_layout.setColumnStretch(
            1,
            1,
        )

        self.add_widget(
            metrics_widget
        )

    @property
    def queue_value(
        self,
    ):
        return self.queue_metric.value_label

    @property
    def mailbox_count_value(
        self,
    ):
        return self.mailbox_metric.value_label

    @property
    def smtp_connections_value(
        self,
    ):
        return (
            self.smtp_connections_metric
            .value_label
        )

    @property
    def imap_connections_value(
        self,
    ):
        return (
            self.imap_connections_metric
            .value_label
        )

    def refresh_view(
        self,
    ) -> None:
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
