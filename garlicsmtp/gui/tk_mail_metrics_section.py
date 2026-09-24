# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.application import (
    ApplicationViewModel,
)
from garlicsmtp.gui.tk_dashboard_widgets import (
    DashboardCard,
    MetricValue,
)


class MailMetricsSection(DashboardCard):

    def __init__(
        self,
        master,
        *,
        view_model: ApplicationViewModel,
    ) -> None:
        super().__init__(
            master,
            title="Mail activity",
        )

        self.view_model = view_model

        self.queue_metric = MetricValue(
            self.content,
            label="Queue",
        )
        self.mailbox_metric = MetricValue(
            self.content,
            label="Mailboxes",
        )
        self.smtp_connections_metric = (
            MetricValue(
                self.content,
                label="SMTP connections",
            )
        )
        self.imap_connections_metric = (
            MetricValue(
                self.content,
                label="IMAP connections",
            )
        )

        self.queue_metric.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 9),
            pady=(0, 7),
        )
        self.mailbox_metric.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(9, 0),
            pady=(0, 7),
        )
        self.smtp_connections_metric.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=(0, 9),
            pady=(7, 0),
        )
        self.imap_connections_metric.grid(
            row=1,
            column=1,
            sticky="nsew",
            padx=(9, 0),
            pady=(7, 0),
        )

        self.content.columnconfigure(
            0,
            weight=1,
        )
        self.content.columnconfigure(
            1,
            weight=1,
        )

    @property
    def queue_value(self):
        return self.queue_metric.value

    @property
    def mailbox_count_value(self):
        return self.mailbox_metric.value

    @property
    def smtp_connections_value(self):
        return (
            self.smtp_connections_metric.value
        )

    @property
    def imap_connections_value(self):
        return (
            self.imap_connections_metric.value
        )

    def refresh_view(
        self,
    ) -> None:
        self.queue_metric.set_text(
            self.view_model
            .pending_messages_text
        )
        self.mailbox_metric.set_text(
            self.view_model
            .mailbox_count_text
        )
        self.smtp_connections_metric.set_text(
            self.view_model
            .smtp_connections_text
        )
        self.imap_connections_metric.set_text(
            self.view_model
            .imap_connections_text
        )
