from pathlib import Path

from garlicsmtp.application import (
    TorStatus,
    TorStatusProvider,
)
from garlicsmtp.configuration import (
    TorSettings,
)


def test_tor_settings_are_secure_by_default():
    settings = TorSettings()

    assert settings.control_enabled is False
    assert settings.require_safecookie is True
    assert settings.allow_new_circuits is False
    assert settings.cookie_file is None


def test_tor_status_reports_endpoints():
    status = TorStatusProvider(
        TorSettings()
    ).snapshot()

    assert status.socks_endpoint == (
        "127.0.0.1:9050"
    )

    assert status.control_endpoint == (
        "127.0.0.1:9051"
    )


def test_tor_control_is_disabled_by_default():
    status = TorStatusProvider(
        TorSettings()
    ).snapshot()

    assert status.control_enabled is False
    assert status.control_available is False
    assert status.authenticated is False
    assert status.ready is False

    assert status.last_error == (
        "Tor control is disabled"
    )


def test_tor_status_never_reports_ready_without_authentication():
    status = TorStatus(
        enabled=True,
        socks_host="127.0.0.1",
        socks_port=9050,
        socks_available=True,
        control_enabled=True,
        control_host="127.0.0.1",
        control_port=9051,
        control_available=True,
        authenticated=False,
        authentication_method="SAFECOOKIE",
        version=None,
        bootstrap_progress=None,
        bootstrap_summary=None,
        built_circuits=0,
        active_streams=0,
        new_circuits_allowed=False,
        new_circuits_available=False,
        last_error=None,
    )

    assert status.ready is False


def test_tor_cookie_path_is_supported():
    settings = TorSettings(
        cookie_file=Path(
            "/run/tor/control.authcookie"
        )
    )

    assert settings.cookie_file == Path(
        "/run/tor/control.authcookie"
    )
