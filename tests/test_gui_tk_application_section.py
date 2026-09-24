# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import tkinter as tk

from garlicsmtp.application import (
    ApplicationViewModel,
)
from garlicsmtp.gui.tk_application_section import (
    ApplicationSection,
)
from tests.support import (
    FakeController,
    make_application_status,
)


def test_application_section_displays_status():
    root = tk.Tk()
    root.withdraw()

    try:
        controller = FakeController()
        controller.current_status = (
            make_application_status()
        )

        view_model = ApplicationViewModel(
            controller
        )

        section = ApplicationSection(
            root,
            view_model=view_model,
        )

        section.refresh_view()

        assert (
            section.runtime_value.get()
            == "Stopped"
        )
        assert (
            section.hostname_value.get()
            == "garlicsmtp.local"
        )
        assert (
            section.domain_value.get()
            == "test.onion"
        )

    finally:
        root.destroy()
