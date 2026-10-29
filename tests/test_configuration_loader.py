# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import pytest

from garlicsmtp.configuration import (
    ConfigurationLoader,
)


def test_configuration_loader_returns_defaults_when_missing(
    tmp_path,
):
    loader = ConfigurationLoader()

    settings = loader.load(
        tmp_path / "missing.toml"
    )

    assert settings.hostname == "garlicsmtp.local"
    assert settings.smtp.host == "127.0.0.1"
    assert settings.smtp.port == 2525
    assert settings.imap.port == 1143
    assert settings.tor.enabled is True


def test_configuration_loader_reads_toml(
    tmp_path,
):
    path = tmp_path / "settings.toml"

    path.write_text(
        """
hostname = "mail.example.onion"
local_domain = "example.onion"

[smtp]
host = "127.0.0.2"
port = 2500

[imap]
host = "127.0.0.3"
port = 1400

[logging]
level = "DEBUG"

[tor]
enabled = false
socks_host = "127.0.0.4"
socks_port = 9150
""".strip(),
        encoding="utf-8",
    )

    loader = ConfigurationLoader()

    settings = loader.load(
        path
    )

    assert settings.hostname == (
        "mail.example.onion"
    )

    assert settings.local_domain == (
        "example.onion"
    )

    assert settings.smtp.host == (
        "127.0.0.2"
    )

    assert settings.smtp.port == 2500
    assert settings.imap.host == "127.0.0.3"
    assert settings.imap.port == 1400
    assert settings.logging.level == "DEBUG"
    assert settings.tor.enabled is False

    assert settings.tor.socks_host == (
        "127.0.0.4"
    )

    assert settings.tor.socks_port == 9150
    assert settings.tor.onion_http_port == 80
    assert settings.tor.onion_http_target_port == 8080
    assert settings.tor.onion_custom_page_enabled is False
    assert settings.tor.onion_custom_page_path is None


def test_configuration_loader_uses_defaults_for_missing_sections(
    tmp_path,
):
    path = tmp_path / "settings.toml"

    path.write_text(
        'hostname = "custom.local"',
        encoding="utf-8",
    )

    settings = ConfigurationLoader().load(
        path
    )

    assert settings.hostname == "custom.local"
    assert settings.smtp.port == 2525
    assert settings.imap.port == 1143
    assert settings.tor.enabled is True


def test_configuration_loader_reads_onion_http_ports(
    tmp_path,
):
    path = tmp_path / "settings.toml"

    path.write_text(
        """
[tor]
onion_http_port = 8081
onion_http_target_port = 18080
""".strip(),
        encoding="utf-8",
    )

    settings = ConfigurationLoader().load(path)

    assert settings.tor.onion_http_port == 8081
    assert settings.tor.onion_http_target_port == 18080


def test_configuration_loader_reads_custom_onion_page_settings(
    tmp_path,
):
    path = tmp_path / "settings.toml"

    path.write_text(
        """
[tor]
onion_custom_page_enabled = true
onion_custom_page_path = "pages/personal.html"
""".strip(),
        encoding="utf-8",
    )

    settings = ConfigurationLoader().load(path)

    assert settings.tor.onion_custom_page_enabled is True
    assert settings.tor.onion_custom_page_path == str(
        tmp_path / "pages" / "personal.html"
    )


def test_configuration_loader_resolves_relative_custom_onion_page_path(
    tmp_path,
):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    path = config_dir / "settings.toml"

    path.write_text(
        """
[tor]
onion_custom_page_enabled = true
onion_custom_page_path = "pages/personal.html"
""".strip(),
        encoding="utf-8",
    )

    settings = ConfigurationLoader().load(path)

    assert settings.tor.onion_custom_page_path == str(
        config_dir / "pages" / "personal.html"
    )


def test_configuration_loader_preserves_absolute_custom_onion_page_path(
    tmp_path,
):
    html_path = tmp_path / "personal.html"
    config_path = tmp_path / "settings.toml"

    config_path.write_text(
        f"""
[tor]
onion_custom_page_enabled = true
onion_custom_page_path = "{html_path.as_posix()}"
""".strip(),
        encoding="utf-8",
    )

    settings = ConfigurationLoader().load(config_path)

    assert settings.tor.onion_custom_page_path == str(html_path)


def test_configuration_loader_ignores_custom_page_path_when_disabled(
    tmp_path,
):
    path = tmp_path / "settings.toml"

    path.write_text(
        """
[tor]
onion_custom_page_enabled = false
onion_custom_page_path = "pages/personal.html"
""".strip(),
        encoding="utf-8",
    )

    settings = ConfigurationLoader().load(path)

    assert settings.tor.onion_custom_page_enabled is False
    assert settings.tor.onion_custom_page_path == "pages/personal.html"


def test_distributed_configuration_disables_custom_onion_page():
    from pathlib import Path
    import tomllib

    project_root = Path(__file__).resolve().parents[1]
    configuration_path = project_root / "config" / "default.toml"

    with configuration_path.open("rb") as configuration_file:
        data = tomllib.load(configuration_file)

    tor = data["tor"]

    assert tor["onion_custom_page_enabled"] is False
    assert tor["onion_custom_page_path"] == ""

    settings = ConfigurationLoader().load(configuration_path)

    assert settings.tor.onion_custom_page_enabled is False
    assert settings.tor.onion_custom_page_path == ""


def test_configuration_rejects_non_loopback_smtp_host(
    tmp_path,
):
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        '[smtp]\nhost = "0.0.0.0"\n',
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="SMTP.*loopback",
    ):
        ConfigurationLoader().load(config_path)


def test_configuration_rejects_non_loopback_imap_host(
    tmp_path,
):
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        '[imap]\nhost = "0.0.0.0"\n',
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="IMAP.*loopback",
    ):
        ConfigurationLoader().load(config_path)