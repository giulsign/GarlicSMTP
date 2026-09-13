# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0

# See LICENSE for the full license terms.

from pathlib import Path

import pytest

from install.tor_runtime import (
    detect_tor_runtime_configuration,
)
from garlicsmtp.tor.control.protocol_info import (
    ProtocolInfo,
    TorAuthenticationMethod,
)


class FakeClient:
    def __init__(self, protocol_info):
        self._protocol_info = protocol_info
        self.connected = False
        self.closed = False

    def connect(self):
        self.connected = True

    def protocol_info(self):
        assert self.connected is True
        return self._protocol_info

    def close(self):
        self.closed = True


def make_protocol_info(
    *,
    methods=None,
    cookie_file=Path(
        "/run/tor/control.authcookie"
    ),
):
    return ProtocolInfo(
        protocol_version=1,
        tor_version="0.4.9.11",
        authentication_methods=frozenset(
            methods
            if methods is not None
            else {
                TorAuthenticationMethod.SAFECOOKIE,
            }
        ),
        cookie_file=cookie_file,
    )


def test_detect_tor_runtime_configuration_uses_protocolinfo_cookie():
    client = FakeClient(
        make_protocol_info()
    )

    configuration = (
        detect_tor_runtime_configuration(
            control_host="127.0.0.1",
            control_port=9051,
            client=client,
            cookie_readable=lambda path: True,
        )
    )

    assert configuration == {
        "control_host": "127.0.0.1",
        "control_port": 9051,
        "cookie_file": Path(
            "/run/tor/control.authcookie"
        ),
    }

    assert client.closed is True


def test_detect_tor_runtime_configuration_requires_safecookie():
    client = FakeClient(
        make_protocol_info(
            methods={
                TorAuthenticationMethod.COOKIE,
            }
        )
    )

    with pytest.raises(
        RuntimeError,
        match="SAFECOOKIE",
    ):
        detect_tor_runtime_configuration(
            control_host="127.0.0.1",
            control_port=9051,
            client=client,
        )

    assert client.closed is True


def test_detect_tor_runtime_configuration_requires_advertised_cookie():
    client = FakeClient(
        make_protocol_info(
            cookie_file=None,
        )
    )

    with pytest.raises(
        RuntimeError,
        match="cookie",
    ):
        detect_tor_runtime_configuration(
            control_host="127.0.0.1",
            control_port=9051,
            client=client,
        )

    assert client.closed is True


def test_detect_tor_runtime_configuration_builds_client_for_endpoint(
    monkeypatch,
):
    created = []

    class Client:
        connected = False
        closed = False

        def connect(self):
            self.connected = True

        def protocol_info(self):
            return make_protocol_info()

        def close(self):
            self.closed = True

    def build_client(*, control_host, control_port):
        created.append(
            (control_host, control_port)
        )
        return Client()

    configuration = detect_tor_runtime_configuration(
        control_host="127.0.0.1",
        control_port=9051,
        client_factory=build_client,
        cookie_readable=lambda path: True,
    )

    assert created == [
        ("127.0.0.1", 9051),
    ]

    assert configuration["cookie_file"] == Path(
        "/run/tor/control.authcookie"
    )


def test_detect_tor_runtime_configuration_rejects_client_and_factory_together():
    client = FakeClient(
        make_protocol_info()
    )

    with pytest.raises(
        ValueError,
        match="client",
    ):
        detect_tor_runtime_configuration(
            control_host="127.0.0.1",
            control_port=9051,
            client=client,
            client_factory=lambda **kwargs: client,
        )


def test_detect_tor_runtime_rejects_unreadable_advertised_cookie():
    client = FakeClient(
        make_protocol_info(
            cookie_file=Path(
                "/run/tor/control.authcookie"
            ),
        )
    )

    with pytest.raises(
        RuntimeError,
        match="cookie.*not readable",
    ):
        detect_tor_runtime_configuration(
            control_host="127.0.0.1",
            control_port=9051,
            client=client,
            cookie_readable=lambda path: False,
        )

    assert client.closed is True