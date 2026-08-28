# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from pathlib import Path

from garlicsmtp.tor.control.client import (
    TorControlClient,
)
from garlicsmtp.tor.control.cookie_reader import (
    SafeCookieReader,
)
from garlicsmtp.tor.control.exceptions import (
    TorControlSecurityError,
)
from garlicsmtp.tor.control.protocol_info import (
    ProtocolInfo,
)
from garlicsmtp.tor.control.safecookie import (
    SafeCookieEngine,
)


class SafeCookieAuthenticator:

    def __init__(
        self,
        *,
        client: TorControlClient,
        cookie_reader: (
            SafeCookieReader | None
        ) = None,
        engine: SafeCookieEngine | None = None,
        configured_cookie_file: (
            Path | None
        ) = None,
    ) -> None:
        self.client = client

        self.cookie_reader = (
            cookie_reader
            or SafeCookieReader()
        )

        self.engine = (
            engine
            or SafeCookieEngine()
        )

        self.configured_cookie_file = (
            configured_cookie_file
        )

    def authenticate(
        self,
    ) -> ProtocolInfo:
        try:
            protocol_info = (
                self.client.protocol_info()
            )

            self._require_safecookie(
                protocol_info
            )

            cookie_path = (
                self._select_cookie_path(
                    protocol_info
                )
            )

            cookie = self.cookie_reader.read(
                cookie_path
            )

            client_nonce = (
                self.engine
                .generate_client_nonce()
            )

            challenge = (
                self.client.auth_challenge(
                    client_nonce
                )
            )

            self.engine.require_valid_server_hash(
                cookie=cookie,
                client_nonce=(
                    challenge.client_nonce
                ),
                server_nonce=(
                    challenge.server_nonce
                ),
                server_hash=(
                    challenge.server_hash
                ),
            )

            client_hash = (
                self.engine.client_hash(
                    cookie=cookie,
                    client_nonce=(
                        challenge.client_nonce
                    ),
                    server_nonce=(
                        challenge.server_nonce
                    ),
                )
            )

            self.client.authenticate_safecookie_hash(
                client_hash
            )

            if not self.client.authenticated:
                raise TorControlSecurityError(
                    "Tor Control authentication "
                    "did not complete"
                )

            return protocol_info

        except Exception:
            self.client.close()
            raise

    @staticmethod
    def _require_safecookie(
        protocol_info: ProtocolInfo,
    ) -> None:
        if not protocol_info.supports_safecookie:
            raise TorControlSecurityError(
                "Tor Control endpoint does not "
                "support SAFECOOKIE"
            )

        if protocol_info.cookie_file is None:
            raise TorControlSecurityError(
                "Tor Control endpoint did not "
                "provide a cookie file"
            )

    def _select_cookie_path(
        self,
        protocol_info: ProtocolInfo,
    ) -> Path:
        advertised_path = (
            protocol_info.cookie_file
        )

        if advertised_path is None:
            raise TorControlSecurityError(
                "Tor Control cookie path "
                "is unavailable"
            )

        configured_path = (
            self.configured_cookie_file
        )

        if configured_path is None:
            return advertised_path

        if not configured_path.is_absolute():
            raise TorControlSecurityError(
                "Configured Tor cookie path "
                "must be absolute"
            )

        if configured_path != advertised_path:
            raise TorControlSecurityError(
                "Configured Tor cookie path "
                "does not match the path "
                "advertised by Tor"
            )

        return configured_path
