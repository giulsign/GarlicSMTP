# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.application import (
    ApplicationViewModel,
)
from garlicsmtp.gui.sections import (
    TorSection,
)
from tests.support import (
    make_application_status,
    make_tor_status,
)

from tests.test_gui_main_window import (
    FakeController,
    get_application,
)
from dataclasses import replace


def test_tor_section_displays_status():
    get_application()

    controller = FakeController()

    controller.current_status = (
        make_application_status(
            tor=make_tor_status(
                control_enabled=True,
                control_available=True,
                authenticated=True,
                authentication_method=(
                    "SAFECOOKIE"
                ),
                socks_available=True,
                version="0.4.8.12",
                bootstrap_progress=100,
                bootstrap_summary="Done",
                built_circuits=3,
                active_streams=1,
                last_error=None,
                socks_listeners=(
                    "127.0.0.1:9050",
                ),
                control_listeners=(
                    "127.0.0.1:9051",
                ), 
                onion_hostname=(
                    ("a" * 56)
                    + ".onion"
                ),
            )
        )
    )

    view_model = ApplicationViewModel(
        controller
    )

    section = TorSection(
        view_model=view_model
    )

    section.refresh_view()

    assert (
        section.status_value.text()
        == "Ready"
    )

    assert (
        section.socks_value.text()
        == "127.0.0.1:9050"
    )

    assert (
        section.control_value.text()
        == "127.0.0.1:9051"
    )

    assert (
        section.authentication_value.text()
        == "SAFECOOKIE"
    )

    assert (
        section.version_value.text()
        == "0.4.8.12"
    )

    assert (
        section.bootstrap_value.text()
        == "100% — Done"
    )

    assert (
        section.circuits_value.text()
        == "3 built circuits"
    )

    assert (
        section.streams_value.text()
        == "1 active stream"
    )

    assert (
    section.onion_smtp_value.text()
        == (
            ("a" * 56)
            + ".onion:25"
        )
    )

    assert (
        section.error_value.text()
        == "None"
    )

    section.close()


def test_tor_section_shows_onion_smtp_address():
    get_application()

    view_model = ApplicationViewModel(
        FakeController()
    )

    view_model._status = replace(
        view_model.status,
        tor=replace(
            view_model.status.tor,
            onion_hostname=(
                ("a" * 56)
                + ".onion"
            ),
            onion_smtp_port=25,
        ),
    )

    section = TorSection(
        view_model=view_model
    )

    section.refresh_view()

    assert (
        section.onion_smtp_value.text()
        == (
            ("a" * 56)
            + ".onion:25"
        )
    )

    section.close()
