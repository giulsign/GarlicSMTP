# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from pathlib import Path

from garlicsmtp.gui.onion_page_gui_factory import (
    create_onion_page_preferences,
)


def test_factory_uses_explicit_settings_path(tmp_path):
    settings_path = tmp_path / "custom.toml"

    preferences = create_onion_page_preferences(
        settings_path,
    )

    assert preferences.settings_path == settings_path


def test_factory_accepts_path_like_input(tmp_path):
    settings_path = tmp_path / "settings.toml"

    preferences = create_onion_page_preferences(
        str(settings_path),
    )

    assert preferences.settings_path == settings_path
