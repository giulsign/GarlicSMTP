# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.application import (
    ApplicationViewModel,
)
from garlicsmtp.gui.sections import (
    ServicesSection,
)
from tests.support import (
    make_application_status,
)

from tests.test_gui_main_window import (
    FakeController,
    get_application,
)


def test_services_section_displays_status():
    get_application()

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
        view_model=view_model
    )

    section.refresh_view()

    assert (
        section.smtp_value.text()
        == "Running"
    )

    assert (
        section.imap_value.text()
        == "Running"
    )

    assert (
        section.worker_value.text()
        == "Running"
    )

    assert (
        section.smtp_endpoint_value.text()
        == "127.0.0.1:2525"
    )

    assert (
        section.imap_endpoint_value.text()
        == "127.0.0.1:1143"
    )

    section.close()
