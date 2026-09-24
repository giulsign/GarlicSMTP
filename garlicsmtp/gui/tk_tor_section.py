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


class TorSection(DashboardCard):

    def __init__(
        self,
        master,
        *,
        view_model: ApplicationViewModel,
    ) -> None:
        super().__init__(
            master,
            title="Tor",
        )

        self.view_model = view_model

        self.status_value = StatusBadge(
            self.content,
        )
        self.socks_value = SelectableValue(
            self.content,
        )
        self.control_value = SelectableValue(
            self.content,
        )
        self.authentication_value = SelectableValue(
            self.content,
        )
        self.version_value = SelectableValue(
            self.content,
        )
        self.bootstrap_value = SelectableValue(
            self.content,
        )
        self.circuits_value = SelectableValue(
            self.content,
        )
        self.streams_value = SelectableValue(
            self.content,
        )
        self.onion_smtp_value = SelectableValue(
            self.content,
        )
        self.error_value = SelectableValue(
            self.content,
        )

        rows = (
            ("Status", self.status_value),
            ("SOCKS listener", self.socks_value),
            ("Control listener", self.control_value),
            (
                "Authentication",
                self.authentication_value,
            ),
            ("Tor version", self.version_value),
            ("Bootstrap", self.bootstrap_value),
            (
                "Built circuits",
                self.circuits_value,
            ),
            (
                "Active streams",
                self.streams_value,
            ),
            (
                "Onion SMTP port",
                self.onion_smtp_value,
            ),
            ("Last error", self.error_value),
        )

        for row, (label, value) in enumerate(rows):
            self.add_row(
                row,
                label,
                value,
            )

    def refresh_view(
        self,
    ) -> None:
        self.status_value.set_status(
            text=self.view_model.tor_status_text,
            status_key=self.view_model.tor_status_key,
        )

        values = (
            (
                self.socks_value,
                self.view_model
                .tor_socks_endpoint_text,
            ),
            (
                self.control_value,
                self.view_model
                .tor_control_endpoint_text,
            ),
            (
                self.authentication_value,
                self.view_model
                .tor_authentication_text,
            ),
            (
                self.version_value,
                self.view_model
                .tor_version_text,
            ),
            (
                self.bootstrap_value,
                self.view_model
                .tor_bootstrap_text,
            ),
            (
                self.circuits_value,
                self.view_model
                .tor_circuits_text,
            ),
            (
                self.streams_value,
                self.view_model
                .tor_streams_text,
            ),
            (
                self.onion_smtp_value,
                self.view_model
                .tor_onion_smtp_text,
            ),
            (
                self.error_value,
                self.view_model
                .tor_error_text,
            ),
        )

        for widget, text in values:
            widget.set_text(text)
