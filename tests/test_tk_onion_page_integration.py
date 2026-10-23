# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import inspect
from pathlib import Path
import inspect
import textwrap

from garlicsmtp.gui.tk_main_window import MainWindow
from garlicsmtp.configuration.paths import ApplicationPaths
from garlicsmtp.gui.tk_onion_page_section import OnionPageSection


def test_main_window_accepts_onion_settings_path():
    parameters = inspect.signature(
        MainWindow.__init__
    ).parameters

    assert "onion_settings_path" in parameters
    assert parameters["onion_settings_path"].kind is (
        inspect.Parameter.KEYWORD_ONLY
    )


def test_onion_settings_path_uses_application_paths_override(
    tmp_path,
):
    custom_file = tmp_path / "custom-settings.toml"

    paths = ApplicationPaths(
        root_dir=tmp_path / "application",
        configuration_file=custom_file,
    )

    assert paths.settings_file == custom_file


def test_main_window_exposes_onion_page_section():
    assert hasattr(
        MainWindow,
        "_create_onion_page_section",
    )


def test_main_window_creates_onion_page_section_with_settings_path(
    tmp_path,
    monkeypatch,
):
    import garlicsmtp.gui.tk_main_window as main_window_module

    settings_path = tmp_path / "settings.toml"
    calls = []

    class FakePreferences:
        pass

    preferences = FakePreferences()

    def fake_factory(path):
        calls.append(("factory", path))
        return preferences

    def fake_section(parent, *, preferences):
        calls.append(("section", parent, preferences))
        return object()

    monkeypatch.setattr(
        main_window_module,
        "create_onion_page_preferences",
        fake_factory,
        raising=False,
    )

    monkeypatch.setattr(
        main_window_module,
        "OnionPageSection",
        fake_section,
        raising=False,
    )

    window = MainWindow.__new__(MainWindow)
    parent = object()

    result = window._create_onion_page_section(
        parent,
        settings_path,
    )

    assert calls == [
        ("factory", settings_path),
        ("section", parent, preferences),
    ]
    assert result is not None




def test_main_window_places_onion_page_section():
    import inspect
    import textwrap

    source = textwrap.dedent(
        inspect.getsource(MainWindow.__init__)
    )

    assert (
        "self.onion_page_section = self._create_onion_page_section("
        in source
    )
    assert "self.onion_page_section.grid(" in source
    assert "columnspan=3" in source


def test_main_window_reserves_row_for_onion_preferences():
    import inspect
    import textwrap

    source = textwrap.dedent(
        inspect.getsource(MainWindow.__init__)
    )

    assert "messages_row = 3" in source
    assert "row=3" in source
    assert "messages_row = 4" in source