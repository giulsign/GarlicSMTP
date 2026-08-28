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


class TorSection(DashboardCard):

    def __init__(
        self,
        *,
        view_model: ApplicationViewModel,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            "Tor",
            parent=parent,
        )

        self.view_model = view_model

        self.status_value = StatusBadge()
        self.socks_value = QLabel()
        self.control_value = QLabel()
        self.authentication_value = QLabel()
        self.version_value = QLabel()
        self.bootstrap_value = QLabel()
        self.circuits_value = QLabel()
        self.streams_value = QLabel()
        self.onion_smtp_value = QLabel()
        self.error_value = QLabel()

        self.error_value.setWordWrap(
            True
        )

        self.add_row(
            "Status",
            self.status_value,
        )

        self.add_row(
            "SOCKS listener",
            self.socks_value,
        )

        self.add_row(
            "Control listener",
            self.control_value,
        )

        self.add_row(
            "Authentication",
            self.authentication_value,
        )

        self.add_row(
            "Tor version",
            self.version_value,
        )

        self.add_row(
            "Bootstrap",
            self.bootstrap_value,
        )

        self.add_row(
            "Built circuits",
            self.circuits_value,
        )

        self.add_row(
            "Active streams",
            self.streams_value,
        )

        self.add_row(
            "Onion SMTP port",
            self.onion_smtp_value,
        )

        self.add_row(
            "Last error",
            self.error_value,
        )

    def refresh_view(
        self,
    ) -> None:
        self.status_value.set_status(
            text=(
                self.view_model
                .tor_status_text
            ),
            status_key=(
                self.view_model
                .tor_status_key
            ),
        )

        self.socks_value.setText(
            self.view_model
            .tor_socks_endpoint_text
        )

        self.control_value.setText(
            self.view_model
            .tor_control_endpoint_text
        )

        self.authentication_value.setText(
            self.view_model
            .tor_authentication_text
        )

        self.version_value.setText(
            self.view_model
            .tor_version_text
        )

        self.bootstrap_value.setText(
            self.view_model
            .tor_bootstrap_text
        )

        self.circuits_value.setText(
            self.view_model
            .tor_circuits_text
        )

        self.streams_value.setText(
            self.view_model
            .tor_streams_text
        )

        self.onion_smtp_value.setText(
            self.view_model
            .tor_onion_smtp_text
        )

        self.error_value.setText(
            self.view_model
            .tor_error_text
        )
