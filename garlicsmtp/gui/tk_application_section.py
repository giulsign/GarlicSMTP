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


class ApplicationSection(DashboardCard):

    def __init__(
        self,
        master,
        *,
        view_model: ApplicationViewModel,
    ) -> None:
        super().__init__(
            master,
            title="Application",
        )

        self.view_model = view_model

        self.runtime_value = StatusBadge(
            self.content,
        )
        self.hostname_value = SelectableValue(
            self.content,
        )
        self.domain_value = SelectableValue(
            self.content,
        )

        self.add_row(
            0,
            "Runtime",
            self.runtime_value,
        )
        self.add_row(
            1,
            "Hostname",
            self.hostname_value,
        )
        self.add_row(
            2,
            "Local domain",
            self.domain_value,
        )

    def refresh_view(
        self,
    ) -> None:
        self.runtime_value.set_status(
            text=self.view_model.runtime_text,
            status_key=(
                self.view_model.runtime_status_key
            ),
        )
        self.hostname_value.set_text(
            self.view_model.hostname
        )
        self.domain_value.set_text(
            self.view_model.local_domain
        )
