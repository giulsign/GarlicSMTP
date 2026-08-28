# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from pathlib import Path

from garlicsmtp.application import (
    TorStatusProvider,
)
from garlicsmtp.configuration import (
    TorSettings,
)
from garlicsmtp.tor.control import (
    TorAuthenticationMethod,
)
from garlicsmtp.tor.control.protocol_info import (
    ProtocolInfo,
)


class FakeAuthenticatedClient:

    def __init__(
        self,
        *,
        values=None,
        error=None,
    ):
        self.values = values or {}
        self.error = error

        self.connected = False
        self.authenticated = False
        self.closed = False

    def connect(self):
        self.connected = True

    def protocol_info(self):
        if self.error is not None:
            raise self.error

        self.authenticated = True

        return ProtocolInfo(
            protocol_version=1,
            tor_version="0.4.8.12",
            authentication_methods=(
                frozenset(
                    {
                        TorAuthenticationMethod
                        .SAFECOOKIE,
                    }
                )
            ),
            cookie_file=Path(
                "/run/tor/"
                "control.authcookie"
            ),
        )

    def auth_challenge(self, client_nonce):
        raise AssertionError(
            "Use an injected authenticator "
            "for this fake"
        )

    def get_info(self, *keys):
        return self.values

    def close(self):
        self.connected = False
        self.closed = True


class FakeAuthenticator:

    def __init__(
        self,
        client,
    ):
        self.client = client

    def authenticate(self):
        info = self.client.protocol_info()
        self.client.authenticated = True
        return info


def test_tor_status_provider_reports_authenticated_status():
    client = FakeAuthenticatedClient(
        values={
            "version": "0.4.8.12",
            "status/bootstrap-phase": (
                "NOTICE BOOTSTRAP "
                "PROGRESS=100 TAG=done "
                'SUMMARY="Done"'
            ),
            "net/listeners/socks": (
                '"127.0.0.1:9050" '
                '"unix:/run/tor/socks"'
            ),
            "net/listeners/control": (
                '"127.0.0.1:9051"'
            ),
            "circuit-status": (
                "18 BUILT path PURPOSE=GENERAL\n"
                "19 LAUNCHED PURPOSE=GENERAL\n"
                "20 BUILT path PURPOSE=HS_CLIENT_REND"
            ),
            "stream-status": (
                "10 SUCCEEDED 18 example.onion:25\n"
                "11 CLOSED 0 example.onion:25"
            ),
        }
    )

    provider = TorStatusProvider(
        TorSettings(
            control_enabled=True,
            cookie_file=Path(
                "/run/tor/"
                "control.authcookie"
            ),
        ),
        client_factory=lambda: client,
        authenticator_factory=(
            FakeAuthenticator
        ),
    )

    status = provider.snapshot()

    assert status.control_available is True
    assert status.authenticated is True
    assert (
        status.authentication_method
        == "SAFECOOKIE"
    )

    assert status.version == "0.4.8.12"
    assert status.bootstrap_progress == 100
    assert status.bootstrap_summary == "Done"
    assert status.bootstrap_complete is True

    assert status.socks_listeners == (
        "127.0.0.1:9050",
        "unix:/run/tor/socks",
    )

    assert status.control_listeners == (
        "127.0.0.1:9051",
    )

    assert status.built_circuits == 2
    assert status.active_streams == 1
    assert status.last_error is None
    assert client.closed is True


def test_tor_status_provider_fails_closed():
    client = FakeAuthenticatedClient(
        error=PermissionError(
            "cookie denied"
        )
    )

    provider = TorStatusProvider(
        TorSettings(
            control_enabled=True
        ),
        client_factory=lambda: client,
        authenticator_factory=(
            FakeAuthenticator
        ),
    )

    status = provider.snapshot()

    assert status.authenticated is False
    assert status.control_available is False
    assert status.version is None

    assert status.last_error == (
        "Tor control status unavailable: "
        "PermissionError"
    )

    assert client.closed is True


def test_tor_status_provider_does_not_connect_when_control_disabled():
    calls = []

    provider = TorStatusProvider(
        TorSettings(
            control_enabled=False
        ),
        client_factory=lambda: (
            calls.append(True)
        ),
    )

    status = provider.snapshot()

    assert status.control_enabled is False
    assert status.authenticated is False
    assert calls == []


def test_tor_status_provider_exposes_onion_hostname():
    service_id = "a" * 56
    onion_hostname = (
        service_id
        + ".onion"
    )

    settings = TorSettings(
        enabled=True,
    )

    provider = TorStatusProvider(
        settings,
        onion_hostname_provider=(
            lambda: onion_hostname
        ),
    )

    status = provider.initial_status()

    assert (
        status.onion_hostname
        == onion_hostname
    )