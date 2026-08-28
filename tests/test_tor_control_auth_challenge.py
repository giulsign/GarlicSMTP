# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import pytest

from garlicsmtp.tor.control import (
    SafeCookieChallengeParser,
    TorControlProtocolError,
    TorControlSecurityError,
    TorReplyParser,
)


def parse_reply(
    *lines: str,
):
    remaining = list(
        lines
    )

    def receive_line():
        if not remaining:
            return None

        return remaining.pop(0)

    return TorReplyParser().parse(
        receive_line
    )


def test_auth_challenge_parser_reads_reply():
    client_nonce = bytes(
        range(32)
    )

    server_hash = bytes(
        range(32, 64)
    )

    server_nonce = bytes(
        range(64, 96)
    )

    reply = parse_reply(
        (
            "250 AUTHCHALLENGE "
            f"SERVERHASH={server_hash.hex().upper()} "
            f"SERVERNONCE={server_nonce.hex().upper()}"
        )
    )

    challenge = (
        SafeCookieChallengeParser()
        .parse(
            reply,
            client_nonce=client_nonce,
        )
    )

    assert challenge.client_nonce == (
        client_nonce
    )

    assert challenge.server_hash == (
        server_hash
    )

    assert challenge.server_nonce == (
        server_nonce
    )


def test_auth_challenge_parser_accepts_lowercase_hex():
    client_nonce = b"A" * 32
    server_hash = b"B" * 32
    server_nonce = b"C" * 32

    reply = parse_reply(
        (
            "250 AUTHCHALLENGE "
            f"SERVERHASH={server_hash.hex()} "
            f"SERVERNONCE={server_nonce.hex()}"
        )
    )

    challenge = (
        SafeCookieChallengeParser()
        .parse(
            reply,
            client_nonce=client_nonce,
        )
    )

    assert challenge.server_hash == (
        server_hash
    )

    assert challenge.server_nonce == (
        server_nonce
    )


def test_auth_challenge_parser_accepts_argument_order():
    client_nonce = b"A" * 32
    server_hash = b"B" * 32
    server_nonce = b"C" * 32

    reply = parse_reply(
        (
            "250 AUTHCHALLENGE "
            f"SERVERNONCE={server_nonce.hex()} "
            f"SERVERHASH={server_hash.hex()}"
        )
    )

    challenge = (
        SafeCookieChallengeParser()
        .parse(
            reply,
            client_nonce=client_nonce,
        )
    )

    assert challenge.server_hash == (
        server_hash
    )

    assert challenge.server_nonce == (
        server_nonce
    )



def test_auth_challenge_parser_ignores_unknown_arguments():
    client_nonce = b"A" * 32
    server_hash = b"B" * 32
    server_nonce = b"C" * 32

    reply = parse_reply(
        (
            "250 AUTHCHALLENGE "
            "FUTURE=value "
            f"SERVERHASH={server_hash.hex()} "
            f"SERVERNONCE={server_nonce.hex()}"
        )
    )

    challenge = (
        SafeCookieChallengeParser()
        .parse(
            reply,
            client_nonce=client_nonce,
        )
    )

    assert challenge.server_hash == (
        server_hash
    )



def test_auth_challenge_parser_rejects_error_reply():
    reply = parse_reply(
        "515 Authentication failed"
    )

    with pytest.raises(
        TorControlProtocolError
    ):
        SafeCookieChallengeParser().parse(
            reply,
            client_nonce=b"A" * 32,
        )


def test_auth_challenge_parser_requires_challenge_line():
    reply = parse_reply(
        "250 OK"
    )

    with pytest.raises(
        TorControlProtocolError
    ):
        SafeCookieChallengeParser().parse(
            reply,
            client_nonce=b"A" * 32,
        )



def test_auth_challenge_parser_requires_server_hash():
    server_nonce = b"C" * 32

    reply = parse_reply(
        (
            "250 AUTHCHALLENGE "
            f"SERVERNONCE={server_nonce.hex()}"
        )
    )

    with pytest.raises(
        TorControlProtocolError
    ):
        SafeCookieChallengeParser().parse(
            reply,
            client_nonce=b"A" * 32,
        )



def test_auth_challenge_parser_requires_server_nonce():
    server_hash = b"B" * 32

    reply = parse_reply(
        (
            "250 AUTHCHALLENGE "
            f"SERVERHASH={server_hash.hex()}"
        )
    )

    with pytest.raises(
        TorControlProtocolError
    ):
        SafeCookieChallengeParser().parse(
            reply,
            client_nonce=b"A" * 32,
        )



def test_auth_challenge_parser_rejects_invalid_server_hash():
    reply = parse_reply(
        (
            "250 AUTHCHALLENGE "
            f"SERVERHASH={'Z' * 64} "
            f"SERVERNONCE={'A' * 64}"
        )
    )

    with pytest.raises(
        TorControlProtocolError
    ):
        SafeCookieChallengeParser().parse(
            reply,
            client_nonce=b"A" * 32,
        )


@pytest.mark.parametrize(
    "server_nonce",
    [
        "AA",
        "A" * 62,
        "A" * 66,
    ],
)
def test_auth_challenge_parser_rejects_invalid_server_nonce_length(
    server_nonce,
):
    reply = parse_reply(
        (
            "250 AUTHCHALLENGE "
            f"SERVERHASH={'B' * 64} "
            f"SERVERNONCE={server_nonce}"
        )
    )

    with pytest.raises(
        TorControlProtocolError
    ):
        SafeCookieChallengeParser().parse(
            reply,
            client_nonce=b"A" * 32,
        )


@pytest.mark.parametrize(
    "client_nonce",
    [
        b"",
        b"A" * 31,
        b"A" * 33,
    ],
)




def test_auth_challenge_parser_rejects_invalid_client_nonce(
    client_nonce,
):
    reply = parse_reply(
        (
            "250 AUTHCHALLENGE "
            f"SERVERHASH={'B' * 64} "
            f"SERVERNONCE={'C' * 64}"
        )
    )

    with pytest.raises(
        TorControlSecurityError
    ):
        SafeCookieChallengeParser().parse(
            reply,
            client_nonce=client_nonce,
        )



def test_auth_challenge_parser_rejects_duplicate_arguments():
    reply = parse_reply(
        (
            "250 AUTHCHALLENGE "
            f"SERVERHASH={'B' * 64} "
            f"SERVERHASH={'C' * 64} "
            f"SERVERNONCE={'D' * 64}"
        )
    )

    with pytest.raises(
        TorControlProtocolError
    ):
        SafeCookieChallengeParser().parse(
            reply,
            client_nonce=b"A" * 32,
        )


def test_auth_challenge_parser_rejects_multiple_challenge_lines():
    reply = parse_reply(
        (
            "250-AUTHCHALLENGE "
            f"SERVERHASH={'B' * 64} "
            f"SERVERNONCE={'C' * 64}"
        ),
        (
            "250-AUTHCHALLENGE "
            f"SERVERHASH={'D' * 64} "
            f"SERVERNONCE={'E' * 64}"
        ),
        "250 OK",
    )

    with pytest.raises(
        TorControlProtocolError
    ):
        SafeCookieChallengeParser().parse(
            reply,
            client_nonce=b"A" * 32,
        )




