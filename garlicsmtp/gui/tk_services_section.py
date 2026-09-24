# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.


from garlicsmtp.application import (
    ApplicationViewModel,
)
from garlicsmtp.gui.tk_dashboard_widgets import (
    DashboardCard,
    SelectableValue,
    StatusBadge,
)


class ServicesSection(DashboardCard):

    def __init__(
        self,
        master,
        *,
        view_model: ApplicationViewModel,
    ) -> None:
        super().__init__(
            master,
            title="Services",
        )

        self.view_model = view_model

        self.smtp_value = StatusBadge(
            self.content,
        )
        self.smtp_endpoint_value = SelectableValue(
            self.content,
        )

        self.imap_value = StatusBadge(
            self.content,
        )
        self.imap_endpoint_value = SelectableValue(
            self.content,
        )

        self.worker_value = StatusBadge(
            self.content,
        )

        self.add_row(
            0,
            "SMTP",
            self.smtp_value,
        )
        self.add_row(
            1,
            "SMTP listener",
            self.smtp_endpoint_value,
        )
        self.add_row(
            2,
            "IMAP",
            self.imap_value,
        )
        self.add_row(
            3,
            "IMAP listener",
            self.imap_endpoint_value,
        )
        self.add_row(
            4,
            "Queue worker",
            self.worker_value,
        )

    def refresh_view(
        self,
    ) -> None:
        self.smtp_value.set_status(
            text=self.view_model.smtp.status_text,
            status_key=self.view_model.smtp.status_key,
        )

        self.imap_value.set_status(
            text=self.view_model.imap.status_text,
            status_key=self.view_model.imap.status_key,
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

        self.smtp_endpoint_value.set_text(
            self.view_model.smtp_endpoint_text
        )

        self.imap_endpoint_value.set_text(
            self.view_model.imap_endpoint_text
        )
