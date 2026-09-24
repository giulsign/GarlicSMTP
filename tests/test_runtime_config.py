# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0

# See LICENSE for the full license terms.

from pathlib import Path
import pytest

from garlicsmtp.runtime_config import (
    detect_tor_runtime_configuration,
)
from garlicsmtp.runtime_config import (
    create_runtime_configuration,
)
from garlicsmtp.configuration import (
    ApplicationSettings,
    TorSettings,
)
from garlicsmtp.runtime_config import (
    validate_runtime_configuration,
)


def test_detect_tor_runtime_configuration_uses_advertised_cookie():
    cookie_file = Path(
        "/run/tor/control.authcookie"
    )

    class ProtocolInfo:
        supports_safecookie = True


    protocol_info = ProtocolInfo()
    protocol_info.cookie_file = cookie_file

    class FakeClient:
        def __init__(self):
            self.calls = []

        def connect(self):
            self.calls.append("connect")

        def protocol_info(self):
            self.calls.append("protocol_info")
            return protocol_info

        def close(self):
            self.calls.append("close")

    client = FakeClient()

    result = detect_tor_runtime_configuration(
        control_host="127.0.0.1",
        control_port=9051,
        client=client,
        cookie_readable=lambda path: True,
    )

    assert result == {
        "control_host": "127.0.0.1",
        "control_port": 9051,
        "cookie_file": cookie_file,
    }

    assert client.calls == [
        "connect",
        "protocol_info",
        "close",
    ]


from garlicsmtp.runtime_config import (
    create_runtime_configuration,
    detect_tor_runtime_configuration,
)


def test_create_runtime_configuration_writes_minimal_tor_settings(
    tmp_path,
):
    settings_file = (
        tmp_path
        / "config"
        / "settings.toml"
    )

    create_runtime_configuration(
        settings_file=settings_file,
        tor_configuration={
            "control_host": "127.0.0.1",
            "control_port": 9051,
            "cookie_file": "/run/tor/control.authcookie",
        },
    )

    assert settings_file.read_text(
        encoding="utf-8",
    ) == (
        "[tor]\n"
        "control_enabled = true\n"
        'control_host = "127.0.0.1"\n'
        "control_port = 9051\n"
        'cookie_file = "/run/tor/control.authcookie"\n'
    )


def test_validate_runtime_configuration_rejects_disabled_tor_control():
    settings = ApplicationSettings(
        tor=TorSettings(
            control_enabled=False,
            cookie_file=Path(
                "/run/tor/control.authcookie"
            ),
        )
    )

    with pytest.raises(
        RuntimeError,
        match="Tor Control must be enabled",
    ):
        validate_runtime_configuration(
            settings,
        )


def test_validate_runtime_configuration_rejects_missing_cookie_file():
    settings = ApplicationSettings(
        tor=TorSettings(
            control_enabled=True,
            cookie_file=None,
        )
    )

    with pytest.raises(
        RuntimeError,
        match="Tor Control cookie file is required",
    ):
        validate_runtime_configuration(
            settings,
        )


def test_validate_runtime_configuration_rejects_disabled_safecookie_requirement():
    settings = ApplicationSettings(
        tor=TorSettings(
            control_enabled=True,
            cookie_file=Path(
                "/run/tor/control.authcookie"
            ),
            require_safecookie=False,
        )
    )

    with pytest.raises(
        RuntimeError,
        match="SAFECOOKIE must be required",
    ):
        validate_runtime_configuration(
            settings,
        )


def test_validate_runtime_configuration_rejects_disabled_tor():
    settings = ApplicationSettings(
        tor=TorSettings(
            enabled=False,
            control_enabled=True,
            cookie_file=Path(
                "/run/tor/control.authcookie"
            ),
            require_safecookie=True,
        )
    )

    with pytest.raises(
        RuntimeError,
        match="Tor must be enabled",
    ):
        validate_runtime_configuration(
            settings,
        )


def test_validate_runtime_configuration_rejects_unreadable_cookie_file():
    cookie_file = Path(
        "/run/tor/control.authcookie"
    )

    settings = ApplicationSettings(
        tor=TorSettings(
            enabled=True,
            control_enabled=True,
            cookie_file=cookie_file,
            require_safecookie=True,
        )
    )

    with pytest.raises(
        RuntimeError,
        match="Tor Control cookie is not readable",
    ):
        validate_runtime_configuration(
            settings,
            cookie_readable=lambda path: False,
        )