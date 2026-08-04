from PySide6.QtWidgets import (
    QLabel,
    QWidget,
)

from garlicsmtp.application import (
    ApplicationViewModel,
)
from garlicsmtp.gui.dashboard_widgets import (
    DashboardCard,
    StatusBadge,
)


class ServicesSection(DashboardCard):

    def __init__(
        self,
        *,
        view_model: ApplicationViewModel,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            "Services",
            parent=parent,
        )

        self.view_model = view_model

        self.smtp_value = StatusBadge()
        self.imap_value = StatusBadge()
        self.worker_value = StatusBadge()

        self.smtp_endpoint_value = QLabel()
        self.imap_endpoint_value = QLabel()

        self.add_row(
            "SMTP",
            self.smtp_value,
        )

        self.add_row(
            "SMTP listener",
            self.smtp_endpoint_value,
        )

        self.add_row(
            "IMAP",
            self.imap_value,
        )

        self.add_row(
            "IMAP listener",
            self.imap_endpoint_value,
        )

        self.add_row(
            "Queue worker",
            self.worker_value,
        )

    def refresh_view(
        self,
    ) -> None:
        self.smtp_value.set_status(
            text=(
                self.view_model
                .smtp
                .status_text
            ),
            status_key=(
                self.view_model
                .smtp
                .status_key
            ),
        )

        self.imap_value.set_status(
            text=(
                self.view_model
                .imap
                .status_text
            ),
            status_key=(
                self.view_model
                .imap
                .status_key
            ),
        )

        self.worker_value.set_status(
            text=(
                self.view_model
                .queue_worker
                .status_text
            ),
            status_key=(
                self.view_model
                .queue_worker
                .status_key
            ),
        )

        self.smtp_endpoint_value.setText(
            self.view_model
            .smtp_endpoint_text
        )

        self.imap_endpoint_value.setText(
            self.view_model
            .imap_endpoint_text
        )
