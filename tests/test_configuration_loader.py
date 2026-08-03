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
