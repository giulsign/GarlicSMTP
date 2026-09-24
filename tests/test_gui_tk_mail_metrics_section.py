# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import tkinter as tk

from garlicsmtp.application import (
    ApplicationViewModel,
)
from garlicsmtp.gui.tk_mail_metrics_section import (
    MailMetricsSection,
)
from tests.support import (
    FakeController,
    make_application_status,
)


def test_mail_metrics_section_displays_metrics():
    root = tk.Tk()
    root.withdraw()

    try:
        controller = FakeController()

        controller.current_status = (
            make_application_status(
                pending_messages=7,
                smtp_connections=2,
                imap_connections=3,
                mailboxes=(
                    "alice@test.onion",
                    "bob@test.onion",
                ),
            )
        )

        section = MailMetricsSection(
            root,
            view_model=ApplicationViewModel(
                controller
            ),
        )

        section.refresh_view()

        assert (
            section.queue_value.get()
            == "7 messages queued"
        )
        assert (
            section.mailbox_count_value.get()
            == "2 mailboxes"
        )
        assert (
            section.smtp_connections_value.get()
            == "2 connections"
        )
        assert (
            section.imap_connections_value.get()
            == "3 connections"
        )

    finally:
        root.destroy()
