# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from pathlib import Path

import pytest

from garlicsmtp.tor.control import (
    SafeCookieAuthenticator,
    SafeCookieEngine,
    TorAuthenticationMethod,
    TorControlSecurityError,
)
from garlicsmtp.tor.control.protocol_info import (
    ProtocolInfo,
)
from garlicsmtp.tor.control.safecookie import (
    SafeCookieChallenge,
)


class DeterministicEngine(
    SafeCookieEngine
):

    def __init__(
        self,
        client_nonce: bytes,
    ):
        self.client_nonce = (
            client_nonce
        )

    def generate_client_nonce(
        self,
    ) -> bytes:
        return self.client_nonce


class FakeCookieReader:

    def __init__(
        self,
        cookie: bytes,
    ):
        self.cookie = cookie
        self.paths = []

    def read(
        self,
        path,
    ):
        self.paths.append(
            path
        )

        return self.cookie


class FakeClient:

    def __init__(
        self,
        *,
        protocol_info,
        challenge,
    ):
        self._protocol_info = (
            protocol_info
        )

        self._challenge = challenge

        self.challenge_nonces = []
        self.authenticated_hashes = []

        self.connected = True
        self.authenticated = False
        self.closed = False

    def protocol_info(
        self,
    ):
        return self._protocol_info

    def auth_challenge(
        self,
        client_nonce,
    ):
        self.challenge_nonces.append(
            client_nonce
        )

        return self._challenge

    def authenticate_safecookie_hash(
        self,
        client_hash,
    ):
        self.authenticated_hashes.append(
            client_hash
        )

        self.authenticated = True

    def close(
        self,
    ):
        self.connected = False
        self.authenticated = False
        self.closed = True


def make_protocol_info(
    *,
    cookie_file=Path(
        "/run/tor/control.authcookie"
    ),
    methods=None,
):
    return ProtocolInfo(
        protocol_version=1,
        tor_version="0.4.8.12",
        authentication_methods=(
            frozenset(
                methods
                or {
                    TorAuthenticationMethod
                    .SAFECOOKIE,
                }
            )
        ),
        cookie_file=cookie_file,
    )


def test_safecookie_authenticator_completes_handshake():
    cookie = b"C" * 32
    client_nonce = b"A" * 32
    server_nonce = b"B" * 32

    engine = DeterministicEngine(
        client_nonce
    )

    server_hash = (
        engine.expected_server_hash(
            cookie=cookie,
            client_nonce=client_nonce,
            server_nonce=server_nonce,
        )
    )

    challenge = SafeCookieChallenge(
        client_nonce=client_nonce,
        server_nonce=server_nonce,
        server_hash=server_hash,
    )

    client = FakeClient(
        protocol_info=make_protocol_info(),
        challenge=challenge,
    )

    cookie_reader = FakeCookieReader(
        cookie
    )

    authenticator = (
        SafeCookieAuthenticator(
            client=client,
            cookie_reader=cookie_reader,
            engine=engine,
        )
    )

    info = authenticator.authenticate()

    expected_client_hash = (
        engine.client_hash(
            cookie=cookie,
            client_nonce=client_nonce,
            server_nonce=server_nonce,
        )
    )

    assert info.supports_safecookie is True

    assert cookie_reader.paths == [
        Path(
            "/run/tor/control.authcookie"
        ),
    ]

    assert client.challenge_nonces == [
        client_nonce,
    ]

    assert client.authenticated_hashes == [
        expected_client_hash,
    ]

    assert client.authenticated is True
    assert client.closed is False


def test_safecookie_authenticator_rejects_bad_server_hash():
    cookie = b"C" * 32
    client_nonce = b"A" * 32
    server_nonce = b"B" * 32

    engine = DeterministicEngine(
        client_nonce
    )

    client = FakeClient(
        protocol_info=make_protocol_info(),
        challenge=SafeCookieChallenge(
            client_nonce=client_nonce,
            server_nonce=server_nonce,
            server_hash=b"X" * 32,
        ),
    )

    authenticator = (
        SafeCookieAuthenticator(
            client=client,
            cookie_reader=(
                FakeCookieReader(
                    cookie
                )
            ),
            engine=engine,
        )
    )

    with pytest.raises(
        TorControlSecurityError
    ):
        authenticator.authenticate()

    assert client.authenticated_hashes == []
    assert client.closed is True


def test_safecookie_authenticator_rejects_other_methods():
    client = FakeClient(
        protocol_info=make_protocol_info(
            methods={
                TorAuthenticationMethod
                .COOKIE,
            }
        ),
        challenge=None,
    )

    authenticator = (
        SafeCookieAuthenticator(
            client=client,
            cookie_reader=(
                FakeCookieReader(
                    b"C" * 32
                )
            ),
        )
    )

    with pytest.raises(
        TorControlSecurityError
    ):
        authenticator.authenticate()

    assert client.challenge_nonces == []
    assert client.authenticated_hashes == []
    assert client.closed is True


def test_safecookie_authenticator_rejects_cookie_path_mismatch():
    client = FakeClient(
        protocol_info=make_protocol_info(
            cookie_file=Path(
                "/run/tor/"
                "control.authcookie"
            )
        ),
        challenge=None,
    )

    authenticator = (
        SafeCookieAuthenticator(
            client=client,
            cookie_reader=(
                FakeCookieReader(
                    b"C" * 32
                )
            ),
            configured_cookie_file=Path(
                "/tmp/other.cookie"
            ),
        )
    )

    with pytest.raises(
        TorControlSecurityError
    ):
        authenticator.authenticate()

    assert client.challenge_nonces == []
    assert client.closed is True


def test_safecookie_authenticator_accepts_matching_configured_path():
    cookie = b"C" * 32
    client_nonce = b"A" * 32
    server_nonce = b"B" * 32

    path = Path(
        "/run/tor/control.authcookie"
    )

    engine = DeterministicEngine(
        client_nonce
    )

    server_hash = (
        engine.expected_server_hash(
            cookie=cookie,
            client_nonce=client_nonce,
            server_nonce=server_nonce,
        )
    )

    client = FakeClient(
        protocol_info=make_protocol_info(
            cookie_file=path
        ),
        challenge=SafeCookieChallenge(
            client_nonce=client_nonce,
            server_nonce=server_nonce,
            server_hash=server_hash,
        ),
    )

    reader = FakeCookieReader(
        cookie
    )

    authenticator = (
        SafeCookieAuthenticator(
            client=client,
            cookie_reader=reader,
            engine=engine,
            configured_cookie_file=path,
        )
    )

    authenticator.authenticate()

    assert reader.paths == [
        path,
    ]

    assert client.authenticated is True


def test_safecookie_authenticator_closes_on_cookie_error():
    class FailingCookieReader:

        def read(
            self,
            path,
        ):
            raise TorControlSecurityError(
                "cookie unavailable"
            )

    client = FakeClient(
        protocol_info=make_protocol_info(),
        challenge=None,
    )

    authenticator = (
        SafeCookieAuthenticator(
            client=client,
            cookie_reader=(
                FailingCookieReader()
            ),
        )
    )

    with pytest.raises(
        TorControlSecurityError
    ):
        authenticator.authenticate()

    assert client.closed is True
