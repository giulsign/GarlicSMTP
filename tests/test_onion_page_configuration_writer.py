# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import tomllib
from pathlib import Path
import os
import stat
import pytest

import garlicsmtp.configuration.onion_page_writer as writer

from garlicsmtp.configuration.onion_page_writer import (
    save_onion_page_settings,
)


def test_save_onion_page_settings_preserves_other_configuration(
    tmp_path,
):
    path = tmp_path / "settings.toml"

    path.write_text(
        '# Keep this comment\n'
        'hostname = "garlicsmtp.local"\n'
        '\n'
        '[smtp]\n'
        'port = 2525\n'
        '\n'
        '[tor]\n'
        'enabled = true\n'
        'socks_port = 9050\n',
        encoding="utf-8",
    )

    save_onion_page_settings(
        path,
        enabled=True,
        html_path="/home/user/personal.html",
    )

    content = path.read_text(encoding="utf-8")
    data = tomllib.loads(content)

    assert "# Keep this comment" in content
    assert data["hostname"] == "garlicsmtp.local"
    assert data["smtp"]["port"] == 2525
    assert data["tor"]["enabled"] is True
    assert data["tor"]["socks_port"] == 9050
    assert data["tor"]["onion_custom_page_enabled"] is True
    assert (
        data["tor"]["onion_custom_page_path"]
        == "/home/user/personal.html"
    )


def test_save_onion_page_settings_updates_existing_values(
    tmp_path,
):
    path = tmp_path / "settings.toml"

    path.write_text(
        '[tor]\n'
        'enabled = true\n'
        'onion_custom_page_enabled = false\n'
        'onion_custom_page_path = "old.html"\n',
        encoding="utf-8",
    )

    save_onion_page_settings(
        path,
        enabled=True,
        html_path="new.html",
    )

    data = tomllib.loads(
        path.read_text(encoding="utf-8")
    )

    assert data["tor"]["onion_custom_page_enabled"] is True
    assert data["tor"]["onion_custom_page_path"] == "new.html"

    content = path.read_text(encoding="utf-8")
    assert content.count("onion_custom_page_enabled =") == 1
    assert content.count("onion_custom_page_path =") == 1


def test_save_onion_page_settings_keeps_default_page_disabled(
    tmp_path,
):
    path = tmp_path / "settings.toml"

    path.write_text(
        '[tor]\n'
        'enabled = true\n',
        encoding="utf-8",
    )

    save_onion_page_settings(
        path,
        enabled=False,
        html_path="",
    )

    data = tomllib.loads(
        path.read_text(encoding="utf-8")
    )

    assert data["tor"]["onion_custom_page_enabled"] is False
    assert data["tor"]["onion_custom_page_path"] == ""
    assert data["tor"]["enabled"] is True



def test_save_onion_page_settings_preserves_inline_comments(
    tmp_path,
):
    path = tmp_path / "settings.toml"

    path.write_text(
        '[tor]\n'
        'enabled = true\n'
        'onion_custom_page_enabled = false # user preference\n'
        'onion_custom_page_path = "old.html" # personal page\n',
        encoding="utf-8",
    )

    save_onion_page_settings(
        path,
        enabled=True,
        html_path="new.html",
    )

    content = path.read_text(encoding="utf-8")
    data = tomllib.loads(content)

    assert "# user preference" in content
    assert "# personal page" in content
    assert data["tor"]["onion_custom_page_enabled"] is True
    assert data["tor"]["onion_custom_page_path"] == "new.html"



def test_save_onion_page_settings_preserves_invalid_original(
    tmp_path,
):
    path = tmp_path / "settings.toml"
    original = '[tor]\nenabled = not_a_boolean\n'

    path.write_text(original, encoding="utf-8")

    with pytest.raises(tomllib.TOMLDecodeError):
        save_onion_page_settings(
            path,
            enabled=True,
            html_path="personal.html",
        )

    assert path.read_text(encoding="utf-8") == original



def test_save_onion_page_settings_uses_atomic_replacement(
    tmp_path,
    monkeypatch,
):
    path = tmp_path / "settings.toml"
    path.write_text('[tor]\nenabled = true\n', encoding="utf-8")

    original_write_text = Path.write_text

    def forbidden_write_text(self, *args, **kwargs):
        if self == path:
            pytest.fail(
                "Configuration must not be overwritten directly"
            )
        return original_write_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", forbidden_write_text)

    save_onion_page_settings(
        path,
        enabled=True,
        html_path="personal.html",
    )

    data = tomllib.loads(path.read_text(encoding="utf-8"))

    assert data["tor"]["onion_custom_page_enabled"] is True
    assert data["tor"]["onion_custom_page_path"] == "personal.html"


@pytest.mark.skipif(
    os.name == "nt",
    reason="POSIX permissions required",
)
def test_save_onion_page_settings_preserves_file_permissions(
    tmp_path,
):
    path = tmp_path / "settings.toml"
    path.write_text(
        "[tor]\nenabled = true\n",
        encoding="utf-8",
    )
    path.chmod(0o600)

    save_onion_page_settings(
        path,
        enabled=True,
        html_path="personal.html",
    )

    assert stat.S_IMODE(path.stat().st_mode) == 0o600

    path.chmod(0o640)

    save_onion_page_settings(
        path,
        enabled=False,
        html_path="",
    )

    assert stat.S_IMODE(path.stat().st_mode) == 0o640


def test_save_onion_page_settings_preserves_original_on_replace_failure(
    tmp_path,
    monkeypatch,
):
    path = tmp_path / "settings.toml"
    original = "[tor]\nenabled = true\n"
    path.write_text(original, encoding="utf-8")

    def fail_replace(source, destination):
        raise OSError("Simulated replacement failure")

    monkeypatch.setattr(
        writer.os,
        "replace",
        fail_replace,
    )

    with pytest.raises(
        OSError,
        match="Simulated replacement failure",
    ):
        save_onion_page_settings(
            path,
            enabled=True,
            html_path="personal.html",
        )

    assert path.read_text(encoding="utf-8") == original
    assert list(tmp_path.iterdir()) == [path]


def test_save_onion_page_settings_escapes_special_path(
    tmp_path,
):
    path = tmp_path / "settings.toml"
    path.write_text("[tor]\n", encoding="utf-8")

    html_path = 'C:\\Users\\Test\\my "page".html'

    save_onion_page_settings(
        path,
        enabled=True,
        html_path=html_path,
    )

    data = tomllib.loads(path.read_text(encoding="utf-8"))

    assert data["tor"]["onion_custom_page_path"] == html_path


def test_save_onion_page_settings_preserves_following_sections(
    tmp_path,
):
    path = tmp_path / "settings.toml"
    path.write_text(
        "[tor]\n"
        "enabled = true\n"
        "\n"
        "[logging]\n"
        'level = "DEBUG"\n',
        encoding="utf-8",
    )

    save_onion_page_settings(
        path,
        enabled=True,
        html_path="personal.html",
    )

    data = tomllib.loads(path.read_text(encoding="utf-8"))

    assert data["tor"]["onion_custom_page_enabled"] is True
    assert data["tor"]["onion_custom_page_path"] == "personal.html"
    assert data["logging"]["level"] == "DEBUG"


def test_save_onion_page_settings_handles_missing_final_newline(
    tmp_path,
):
    path = tmp_path / "settings.toml"

    original = (
        'hostname = "garlicsmtp.local"\n'
        '\n'
        '[tor]\n'
        'enabled = true\n'
        'allow_new_circuits = false'
    )

    path.write_text(original, encoding="utf-8")

    save_onion_page_settings(
        path,
        enabled=True,
        html_path="/home/user/personal.html",
    )

    content = path.read_text(encoding="utf-8")
    data = tomllib.loads(content)

    assert data["hostname"] == "garlicsmtp.local"
    assert data["tor"]["enabled"] is True
    assert data["tor"]["allow_new_circuits"] is False
    assert data["tor"]["onion_custom_page_enabled"] is True
    assert (
        data["tor"]["onion_custom_page_path"]
        == "/home/user/personal.html"
    )

    assert "allow_new_circuits = false\n" in content