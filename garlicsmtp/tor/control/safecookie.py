import hashlib
import hmac
import secrets
from dataclasses import dataclass
from typing import Final

from garlicsmtp.tor.control.exceptions import (
    TorControlProtocolError,
    TorControlSecurityError,
)


SAFECOOKIE_VALUE_BYTES: Final = 32

SERVER_HASH_KEY: Final[bytes] = (
    b"Tor safe cookie authentication "
    b"server-to-controller hash"
)

CLIENT_HASH_KEY: Final[bytes] = (
    b"Tor safe cookie authentication "
    b"controller-to-server hash"
)


@dataclass(
    frozen=True,
    slots=True,
)
class SafeCookieChallenge:

    client_nonce: bytes
    server_nonce: bytes
    server_hash: bytes

    def __post_init__(
        self,
    ) -> None:
        _require_exact_bytes(
            self.client_nonce,
            name="client_nonce",
        )

        _require_exact_bytes(
            self.server_nonce,
            name="server_nonce",
        )

        _require_exact_bytes(
            self.server_hash,
            name="server_hash",
        )


class SafeCookieEngine:

    def generate_client_nonce(
        self,
    ) -> bytes:
        return secrets.token_bytes(
            SAFECOOKIE_VALUE_BYTES
        )

    def expected_server_hash(
        self,
        *,
        cookie: bytes,
        client_nonce: bytes,
        server_nonce: bytes,
    ) -> bytes:
        message = self._build_message(
            cookie=cookie,
            client_nonce=client_nonce,
            server_nonce=server_nonce,
        )

        return hmac.new(
            SERVER_HASH_KEY,
            message,
            hashlib.sha256,
        ).digest()

    def client_hash(
        self,
        *,
        cookie: bytes,
        client_nonce: bytes,
        server_nonce: bytes,
    ) -> bytes:
        message = self._build_message(
            cookie=cookie,
            client_nonce=client_nonce,
            server_nonce=server_nonce,
        )

        return hmac.new(
            CLIENT_HASH_KEY,
            message,
            hashlib.sha256,
        ).digest()

    def verify_server_hash(
        self,
        *,
        cookie: bytes,
        client_nonce: bytes,
        server_nonce: bytes,
        server_hash: bytes,
    ) -> bool:
        _require_exact_bytes(
            server_hash,
            name="server_hash",
        )

        expected = self.expected_server_hash(
            cookie=cookie,
            client_nonce=client_nonce,
            server_nonce=server_nonce,
        )

        return hmac.compare_digest(
            expected,
            server_hash,
        )

    def require_valid_server_hash(
        self,
        *,
        cookie: bytes,
        client_nonce: bytes,
        server_nonce: bytes,
        server_hash: bytes,
    ) -> None:
        if not self.verify_server_hash(
            cookie=cookie,
            client_nonce=client_nonce,
            server_nonce=server_nonce,
            server_hash=server_hash,
        ):
            raise TorControlSecurityError(
                "Tor SAFECOOKIE server "
                "authentication failed"
            )

    @staticmethod
    def encode_hex(
        value: bytes,
    ) -> str:
        _require_exact_bytes(
            value,
            name="value",
        )

        return value.hex().upper()

    @staticmethod
    def decode_hex(
        value: str,
        *,
        name: str = "value",
    ) -> bytes:
        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                f"{name} must be text"
            )

        if len(value) != (
            SAFECOOKIE_VALUE_BYTES * 2
        ):
            raise TorControlProtocolError(
                f"{name} must contain exactly "
                f"{SAFECOOKIE_VALUE_BYTES * 2} "
                "hexadecimal characters"
            )

        try:
            decoded = bytes.fromhex(
                value
            )
        except ValueError as exc:
            raise TorControlProtocolError(
                f"{name} contains invalid "
                "hexadecimal data"
            ) from exc

        _require_exact_bytes(
            decoded,
            name=name,
        )

        return decoded

    @staticmethod
    def _build_message(
        *,
        cookie: bytes,
        client_nonce: bytes,
        server_nonce: bytes,
    ) -> bytes:
        _require_exact_bytes(
            cookie,
            name="cookie",
        )

        _require_exact_bytes(
            client_nonce,
            name="client_nonce",
        )

        _require_exact_bytes(
            server_nonce,
            name="server_nonce",
        )

        return (
            cookie
            + client_nonce
            + server_nonce
        )


def _require_exact_bytes(
    value: bytes,
    *,
    name: str,
) -> None:
    if not isinstance(
        value,
        bytes,
    ):
        raise TypeError(
            f"{name} must be bytes"
        )

    if len(value) != SAFECOOKIE_VALUE_BYTES:
        raise TorControlSecurityError(
            f"{name} must be exactly "
            f"{SAFECOOKIE_VALUE_BYTES} bytes"
        )
