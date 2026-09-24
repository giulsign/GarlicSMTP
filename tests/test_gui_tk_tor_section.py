# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import tkinter as tk
from dataclasses import replace

from garlicsmtp.application import (
    ApplicationViewModel,
)
from garlicsmtp.gui.tk_tor_section import (
    TorSection,
)
from tests.support import (
    FakeController,
    make_application_status,
    make_tor_status,
)


def test_tor_section_displays_status():
    root = tk.Tk()
    root.withdraw()

    try:
        controller = FakeController()

        controller.current_status = (
            make_application_status(
                tor=make_tor_status(
                    control_enabled=True,
                    control_available=True,
                    authenticated=True,
                    authentication_method="SAFECOOKIE",
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
            root,
            view_model=view_model,
        )

        section.refresh_view()

        assert section.status_value.get() == "Ready"
        assert (
            section.status_value.status_key
            == view_model.tor_status_key
        )
        assert (
            section.socks_value.get()
            == "127.0.0.1:9050"
        )
        assert (
            section.control_value.get()
            == "127.0.0.1:9051"
        )
        assert (
            section.authentication_value.get()
            == "SAFECOOKIE"
        )
        assert (
            section.version_value.get()
            == "0.4.8.12"
        )
        assert (
            section.bootstrap_value.get()
            == "100% — Done"
        )
        assert (
            section.circuits_value.get()
            == "3 built circuits"
        )
        assert (
            section.streams_value.get()
            == "1 active stream"
        )
        assert (
            section.onion_smtp_value.get()
            == ("a" * 56) + ".onion:25"
        )
        assert (
            section.error_value.get()
            == "None"
        )

    finally:
        root.destroy()


def test_tor_section_shows_onion_smtp_address():
    root = tk.Tk()
    root.withdraw()

    try:
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
            root,
            view_model=view_model,
        )

        section.refresh_view()

        assert (
            section.onion_smtp_value.get()
            == ("a" * 56) + ".onion:25"
        )

    finally:
        root.destroy()
