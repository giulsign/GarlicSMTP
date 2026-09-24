# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import tkinter as tk

from garlicsmtp.application import (
    ApplicationViewModel,
)
from garlicsmtp.gui.tk_services_section import (
    ServicesSection,
)
from tests.support import (
    FakeController,
    make_application_status,
)


def test_services_section_displays_status():
    root = tk.Tk()
    root.withdraw()

    try:
        controller = FakeController()

        controller.current_status = (
            make_application_status(
                smtp_running=True,
                imap_running=True,
                queue_worker_running=True,
                smtp_host="127.0.0.1",
                smtp_port=2525,
                imap_host="127.0.0.1",
                imap_port=1143,
            )
        )

        view_model = ApplicationViewModel(
            controller
        )

        section = ServicesSection(
            root,
            view_model=view_model,
        )

        section.refresh_view()

        assert (
            section.smtp_value.get()
            == "Running"
        )
        assert (
            section.imap_value.get()
            == "Running"
        )
        assert (
            section.worker_value.get()
            == "Running"
        )

        assert (
            section.smtp_endpoint_value.get()
            == "127.0.0.1:2525"
        )
        assert (
            section.imap_endpoint_value.get()
            == "127.0.0.1:1143"
        )

        assert (
            section.smtp_value.status_key
            == view_model.smtp.status_key
        )
        assert (
            section.imap_value.status_key
            == view_model.imap.status_key
        )
        assert (
            section.worker_value.status_key
            == view_model.queue_worker.status_key
        )

    finally:
        root.destroy()
