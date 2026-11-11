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



def test_onion_page_preferences_loads_website_settings(
    tmp_path,
):
    settings_path = tmp_path / "settings.toml"
    settings_path.write_text(
        "[tor]\n"
        "onion_custom_page_enabled = false\n"
        'onion_custom_page_path = ""\n'
        "onion_website_enabled = true\n"
        'onion_website_index_path = "website/index.html"\n',
        encoding="utf-8",
    )

    preferences = OnionPagePreferences(settings_path)

    assert preferences.load_website() == (
        True,
        "website/index.html",
    )



def test_onion_page_preferences_saves_website(
    tmp_path,
    monkeypatch,
):
    settings_path = tmp_path / "settings.toml"
    calls = []

    def fake_save(path, *, enabled, html_path):
        calls.append((path, enabled, html_path))

    monkeypatch.setattr(
        "garlicsmtp.configuration.onion_page_writer.save_onion_website_settings",
        fake_save,
    )

    preferences = OnionPagePreferences(settings_path)

    preferences.save_website(
        enabled=True,
        html_path="website/index.html",
    )

    assert calls == [
        (
            settings_path,
            True,
            "website/index.html",
        )
    ]



def test_onion_page_preferences_save_combined_uses_atomic_writer(
    tmp_path,
    monkeypatch,
):
    from garlicsmtp.gui.onion_page_preferences import (
        OnionPagePreferences,
    )
    import garlicsmtp.gui.onion_page_preferences as module

    settings_path = tmp_path / "config.toml"
    settings_path.write_text(
        "[tor]\n",
        encoding="utf-8",
    )

    calls = []

    def fake_save_combined(path, **kwargs):
        calls.append((path, kwargs))

    monkeypatch.setattr(
        module.onion_page_writer,
        "save_onion_combined_settings",
        fake_save_combined,
    )

    preferences = OnionPagePreferences(settings_path)

    preferences.save_combined(
        custom_enabled=False,
        custom_html_path="",
        website_enabled=False,
        website_index_path="",
    )

    assert calls == [
        (
            settings_path,
            {
                "custom_enabled": False,
                "custom_html_path": "",
                "website_enabled": False,
                "website_index_path": "",
            },
        ),
    ]



def test_onion_page_preferences_save_combined_rejects_empty_website_path(
    tmp_path,
    monkeypatch,
):
    import pytest
    import garlicsmtp.gui.onion_page_preferences as module

    settings_path = tmp_path / "config.toml"
    settings_path.write_text(
        "[tor]\n",
        encoding="utf-8",
    )

    calls = []

    def fake_save_combined(*args, **kwargs):
        calls.append((args, kwargs))

    monkeypatch.setattr(
        module.onion_page_writer,
        "save_onion_combined_settings",
        fake_save_combined,
    )

    preferences = module.OnionPagePreferences(settings_path)

    with pytest.raises(ValueError, match="HTML path is required"):
        preferences.save_combined(
            custom_enabled=False,
            custom_html_path="",
            website_enabled=True,
            website_index_path="",
        )

    assert calls == []



def test_onion_page_preferences_save_combined_rejects_empty_custom_path(
    tmp_path,
    monkeypatch,
):
    import pytest
    import garlicsmtp.gui.onion_page_preferences as module

    settings_path = tmp_path / "config.toml"
    settings_path.write_text(
        "[tor]\n",
        encoding="utf-8",
    )

    calls = []

    def fake_save_combined(*args, **kwargs):
        calls.append((args, kwargs))

    monkeypatch.setattr(
        module.onion_page_writer,
        "save_onion_combined_settings",
        fake_save_combined,
    )

    preferences = module.OnionPagePreferences(settings_path)

    with pytest.raises(ValueError, match="HTML path is required"):
        preferences.save_combined(
            custom_enabled=True,
            custom_html_path="",
            website_enabled=False,
            website_index_path="",
        )

    assert calls == []



def test_onion_page_preferences_save_combined_rejects_website_directory(
    tmp_path,
    monkeypatch,
):
    import pytest
    import garlicsmtp.gui.onion_page_preferences as module

    settings_path = tmp_path / "config.toml"
    settings_path.write_text(
        "[tor]\n",
        encoding="utf-8",
    )

    website_directory = tmp_path / "website"
    website_directory.mkdir()

    calls = []

    def fake_save_combined(*args, **kwargs):
        calls.append((args, kwargs))

    monkeypatch.setattr(
        module.onion_page_writer,
        "save_onion_combined_settings",
        fake_save_combined,
    )

    preferences = module.OnionPagePreferences(settings_path)

    with pytest.raises(
        ValueError,
        match="must point to a file, not a directory",
    ):
        preferences.save_combined(
            custom_enabled=False,
            custom_html_path="",
            website_enabled=True,
            website_index_path=str(website_directory),
        )

    assert calls == []



def test_onion_page_preferences_save_combined_rejects_custom_directory(
    tmp_path,
    monkeypatch,
):
    import pytest
    import garlicsmtp.gui.onion_page_preferences as module

    settings_path = tmp_path / "config.toml"
    settings_path.write_text(
        "[tor]\n",
        encoding="utf-8",
    )

    custom_directory = tmp_path / "custom"
    custom_directory.mkdir()

    calls = []

    def fake_save_combined(*args, **kwargs):
        calls.append((args, kwargs))

    monkeypatch.setattr(
        module.onion_page_writer,
        "save_onion_combined_settings",
        fake_save_combined,
    )

    preferences = module.OnionPagePreferences(settings_path)

    with pytest.raises(
        ValueError,
        match="must point to a file, not a directory",
    ):
        preferences.save_combined(
            custom_enabled=True,
            custom_html_path=str(custom_directory),
            website_enabled=False,
            website_index_path="",
        )

    assert calls == []
