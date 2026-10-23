# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from pathlib import Path
import tomllib
import pytest

from garlicsmtp.gui.onion_page_preferences import (
    OnionPagePreferences,
)


def test_onion_page_preferences_saves_custom_page(
    tmp_path,
    monkeypatch,
):
    settings_path = tmp_path / "settings.toml"
    calls = []

    def fake_save(path, *, enabled, html_path):
        calls.append((path, enabled, html_path))

    monkeypatch.setattr(
        "garlicsmtp.gui.onion_page_preferences.save_onion_page_settings",
        fake_save,
    )

    preferences = OnionPagePreferences(settings_path)

    preferences.save(
        enabled=True,
        html_path="pages/personal.html",
    )

    assert calls == [
        (
            settings_path,
            True,
            "pages/personal.html",
        )
    ]


def test_onion_page_preferences_saves_default_page(
    tmp_path,
    monkeypatch,
):
    settings_path = tmp_path / "settings.toml"
    calls = []

    def fake_save(path, *, enabled, html_path):
        calls.append((path, enabled, html_path))

    monkeypatch.setattr(
        "garlicsmtp.gui.onion_page_preferences.save_onion_page_settings",
        fake_save,
    )

    preferences = OnionPagePreferences(settings_path)

    preferences.save(
        enabled=False,
        html_path="",
    )

    assert calls == [(settings_path, False, "")]


def test_onion_page_preferences_requires_path_when_enabled(
    tmp_path,
    monkeypatch,
):
    settings_path = tmp_path / "settings.toml"
    calls = []

    def fake_save(path, *, enabled, html_path):
        calls.append((path, enabled, html_path))

    monkeypatch.setattr(
        "garlicsmtp.gui.onion_page_preferences.save_onion_page_settings",
        fake_save,
    )

    preferences = OnionPagePreferences(settings_path)

    with pytest.raises(
        ValueError,
        match="HTML path",
    ):
        preferences.save(
            enabled=True,
            html_path="   ",
        )

    assert calls == []


def test_onion_page_preferences_loads_custom_page(tmp_path):
    settings_path = tmp_path / "settings.toml"
    settings_path.write_text(
        "[tor]\n"
        "onion_custom_page_enabled = true\n"
        'onion_custom_page_path = "pages/personal.html"\n',
        encoding="utf-8",
    )

    preferences = OnionPagePreferences(settings_path)

    assert preferences.load() == (
        True,
        "pages/personal.html",
    )


def test_onion_page_preferences_loads_defaults(tmp_path):
    settings_path = tmp_path / "settings.toml"
    settings_path.write_text(
        "[tor]\n"
        "enabled = true\n",
        encoding="utf-8",
    )

    preferences = OnionPagePreferences(settings_path)

    assert preferences.load() == (False, "")


def test_onion_page_preferences_rejects_invalid_toml(tmp_path):
    settings_path = tmp_path / "settings.toml"
    settings_path.write_text(
        "[tor]\n"
        "enabled = invalid\n",
        encoding="utf-8",
    )

    preferences = OnionPagePreferences(settings_path)

    with pytest.raises(tomllib.TOMLDecodeError):
        preferences.load()


def test_onion_page_preferences_rejects_invalid_enabled_type(
    tmp_path,
):
    settings_path = tmp_path / "settings.toml"
    settings_path.write_text(
        "[tor]\n"
        'onion_custom_page_enabled = "true"\n',
        encoding="utf-8",
    )

    preferences = OnionPagePreferences(settings_path)

    with pytest.raises(
        ValueError,
        match="onion_custom_page_enabled",
    ):
        preferences.load()


def test_onion_page_preferences_rejects_invalid_path_type(
    tmp_path,
):
    settings_path = tmp_path / "settings.toml"
    settings_path.write_text(
        "[tor]\n"
        "onion_custom_page_path = 123\n",
        encoding="utf-8",
    )

    preferences = OnionPagePreferences(settings_path)

    with pytest.raises(
        ValueError,
        match="onion_custom_page_path",
    ):
        preferences.load()


def test_onion_page_preferences_rejects_directory_as_html_file(
    tmp_path,
    monkeypatch,
):
    settings_path = tmp_path / "settings.toml"
    html_directory = tmp_path / "personalized_html"
    html_directory.mkdir()

    calls = []

    def fake_save(path, *, enabled, html_path):
        calls.append((path, enabled, html_path))

    monkeypatch.setattr(
        "garlicsmtp.gui.onion_page_preferences.save_onion_page_settings",
        fake_save,
    )

    preferences = OnionPagePreferences(settings_path)

    with pytest.raises(
        ValueError,
        match="HTML file",
    ):
        preferences.save(
            enabled=True,
            html_path=str(html_directory),
        )

    assert calls == []


def test_onion_page_preferences_rejects_relative_directory(
    tmp_path,
    monkeypatch,
):
    settings_path = tmp_path / "settings.toml"
    (tmp_path / "personalized_html").mkdir()

    calls = []

    def fake_save(path, *, enabled, html_path):
        calls.append((path, enabled, html_path))

    monkeypatch.setattr(
        "garlicsmtp.gui.onion_page_preferences.save_onion_page_settings",
        fake_save,
    )

    preferences = OnionPagePreferences(settings_path)

    with pytest.raises(
        ValueError,
        match="HTML file",
    ):
        preferences.save(
            enabled=True,
            html_path="personalized_html",
        )

    assert calls == []