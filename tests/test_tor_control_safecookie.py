import hashlib
import hmac

import pytest

from garlicsmtp.tor.control import (
    CLIENT_HASH_KEY,
    SERVER_HASH_KEY,
    SafeCookieChallenge,
    SafeCookieEngine,
    TorControlProtocolError,
    TorControlSecurityError,
)


def test_safecookie_computes_server_hash():
    cookie = bytes(range(32))
    client_nonce = bytes(range(32, 64))
    server_nonce = bytes(range(64, 96))

    engine = SafeCookieEngine()

    result = engine.expected_server_hash(
        cookie=cookie,
        client_nonce=client_nonce,
        server_nonce=server_nonce,
    )

    expected = hmac.new(
        SERVER_HASH_KEY,
        (
            cookie
            + client_nonce
            + server_nonce
        ),
        hashlib.sha256,
    ).digest()

    assert result == expected
    assert len(result) == 32


def test_safecookie_computes_client_hash():
    cookie = bytes(range(32))
    client_nonce = bytes(range(32, 64))
    server_nonce = bytes(range(64, 96))

    engine = SafeCookieEngine()

    result = engine.client_hash(
        cookie=cookie,
        client_nonce=client_nonce,
        server_nonce=server_nonce,
    )

    expected = hmac.new(
        CLIENT_HASH_KEY,
        (
            cookie
            + client_nonce
            + server_nonce
        ),
        hashlib.sha256,
    ).digest()

    assert result == expected
    assert len(result) == 32


def test_safecookie_hash_directions_are_distinct():
    cookie = b"C" * 32
    client_nonce = b"A" * 32
    server_nonce = b"B" * 32

    engine = SafeCookieEngine()

    server_hash = (
        engine.expected_server_hash(
            cookie=cookie,
            client_nonce=client_nonce,
            server_nonce=server_nonce,
        )
    )

    client_hash = engine.client_hash(
        cookie=cookie,
        client_nonce=client_nonce,
        server_nonce=server_nonce,
    )

    assert server_hash != client_hash


def test_safecookie_verifies_server_hash():
    cookie = b"C" * 32
    client_nonce = b"A" * 32
    server_nonce = b"B" * 32

    engine = SafeCookieEngine()

    server_hash = (
        engine.expected_server_hash(
            cookie=cookie,
            client_nonce=client_nonce,
            server_nonce=server_nonce,
        )
    )

    assert engine.verify_server_hash(
        cookie=cookie,
        client_nonce=client_nonce,
        server_nonce=server_nonce,
        server_hash=server_hash,
    ) is True


def test_safecookie_rejects_invalid_server_hash():
    engine = SafeCookieEngine()

    assert engine.verify_server_hash(
        cookie=b"C" * 32,
        client_nonce=b"A" * 32,
        server_nonce=b"B" * 32,
        server_hash=b"X" * 32,
    ) is False


def test_safecookie_requires_valid_server_hash():
    engine = SafeCookieEngine()

    with pytest.raises(
        TorControlSecurityError
    ):
        engine.require_valid_server_hash(
            cookie=b"C" * 32,
            client_nonce=b"A" * 32,
            server_nonce=b"B" * 32,
            server_hash=b"X" * 32,
        )


def test_safecookie_generates_32_byte_nonce():
    engine = SafeCookieEngine()

    first = engine.generate_client_nonce()
    second = engine.generate_client_nonce()

    assert isinstance(first, bytes)
    assert len(first) == 32
    assert len(second) == 32
    assert first != second


def test_safecookie_encodes_uppercase_hex():
    value = bytes(range(32))

    encoded = SafeCookieEngine.encode_hex(
        value
    )

    assert encoded == value.hex().upper()
    assert len(encoded) == 64


def test_safecookie_decodes_hex():
    value = bytes(range(32))

    decoded = SafeCookieEngine.decode_hex(
        value.hex().upper(),
        name="server_nonce",
    )

    assert decoded == value


@pytest.mark.parametrize(
    "value",
    [
        "",
        "00",
        "A" * 63,
        "A" * 65,
        "Z" * 64,
    ],
)
def test_safecookie_rejects_invalid_hex(
    value,
):
    with pytest.raises(
        TorControlProtocolError
    ):
        SafeCookieEngine.decode_hex(
            value
        )


@pytest.mark.parametrize(
    (
        "cookie",
        "client_nonce",
        "server_nonce",
    ),
    [
        (
            b"C" * 31,
            b"A" * 32,
            b"B" * 32,
        ),
        (
            b"C" * 33,
            b"A" * 32,
            b"B" * 32,
        ),
        (
            b"C" * 32,
            b"A" * 31,
            b"B" * 32,
        ),
        (
            b"C" * 32,
            b"A" * 32,
            b"B" * 31,
        ),
    ],
)
def test_safecookie_rejects_invalid_lengths(
    cookie,
    client_nonce,
    server_nonce,
):
    engine = SafeCookieEngine()

    with pytest.raises(
        TorControlSecurityError
    ):
        engine.client_hash(
            cookie=cookie,
            client_nonce=client_nonce,
            server_nonce=server_nonce,
        )


def test_safecookie_rejects_non_bytes():
    engine = SafeCookieEngine()

    with pytest.raises(
        TypeError
    ):
        engine.client_hash(
            cookie="C" * 32,
            client_nonce=b"A" * 32,
            server_nonce=b"B" * 32,
        )


def test_safecookie_challenge_accepts_valid_values():
    challenge = SafeCookieChallenge(
        client_nonce=b"A" * 32,
        server_nonce=b"B" * 32,
        server_hash=b"C" * 32,
    )

    assert challenge.client_nonce == (
        b"A" * 32
    )


def test_safecookie_challenge_rejects_invalid_values():
    with pytest.raises(
        TorControlSecurityError
    ):
        SafeCookieChallenge(
            client_nonce=b"A" * 31,
            server_nonce=b"B" * 32,
            server_hash=b"C" * 32,
        )
