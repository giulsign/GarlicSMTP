# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

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


class ApplicationSection(DashboardCard):

    def __init__(
        self,
        *,
        view_model: ApplicationViewModel,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            "Application",
            parent=parent,
        )

        self.view_model = view_model

        self.runtime_value = StatusBadge()
        self.hostname_value = QLabel()
        self.domain_value = QLabel()

        self.add_row(
            "Runtime",
            self.runtime_value,
        )

        self.add_row(
            "Hostname",
            self.hostname_value,
        )

        self.add_row(
            "Local domain",
            self.domain_value,
        )

    def refresh_view(
        self,
    ) -> None:
        self.runtime_value.set_status(
            text=self.view_model.runtime_text,
            status_key=(
                self.view_model
                .runtime_status_key
            ),
        )

        self.hostname_value.setText(
            self.view_model.hostname
        )

        self.domain_value.setText(
            self.view_model.local_domain
        )
