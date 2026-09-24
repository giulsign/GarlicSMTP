# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from pathlib import Path

import pytest

from garlicsmtp.tor.control import (
    ProtocolInfoParser,
    TorAuthenticationMethod,
    TorControlProtocolError,
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


def test_protocol_info_parser_reads_reply():
    reply = parse_reply(
        "250-PROTOCOLINFO 1",
        (
            "250-AUTH "
            "METHODS=SAFECOOKIE,COOKIE "
            'COOKIEFILE="/run/tor/'
            'control.authcookie"'
        ),
        '250-VERSION Tor="0.4.8.12"',
        "250 OK",
    )

    info = ProtocolInfoParser().parse(
        reply
    )

    assert info.protocol_version == 1
    assert info.tor_version == "0.4.8.12"

    assert info.authentication_methods == (
        frozenset(
            {
                TorAuthenticationMethod.SAFECOOKIE,
                TorAuthenticationMethod.COOKIE,
            }
        )
    )

    assert info.cookie_file == Path(
        "/run/tor/control.authcookie"
    )

    assert info.supports_safecookie is True

    assert (
        info.supports_deprecated_cookie
        is True
    )


def test_protocol_info_accepts_lines_in_any_order():
    reply = parse_reply(
        '250-VERSION Tor="0.4.8.12"',
        (
            "250-AUTH "
            "METHODS=SAFECOOKIE "
            'COOKIEFILE="/tmp/cookie"'
        ),
        "250-PROTOCOLINFO 1",
        "250 OK",
    )

    info = ProtocolInfoParser().parse(
        reply
    )

    assert info.protocol_version == 1
    assert info.tor_version == "0.4.8.12"
    assert info.supports_safecookie is True


def test_protocol_info_ignores_unknown_lines():
    reply = parse_reply(
        "250-PROTOCOLINFO 1",
        "250-FUTURE FEATURE=enabled",
        "250-AUTH METHODS=SAFECOOKIE",
        '250-VERSION Tor="0.4.8.12"',
        "250 OK",
    )

    info = ProtocolInfoParser().parse(
        reply
    )

    assert info.protocol_version == 1
    assert info.supports_safecookie is True


def test_protocol_info_ignores_unknown_auth_methods():
    reply = parse_reply(
        "250-PROTOCOLINFO 1",
        (
            "250-AUTH "
            "METHODS=SAFECOOKIE,FUTUREAUTH"
        ),
        "250 OK",
    )

    info = ProtocolInfoParser().parse(
        reply
    )

    assert info.authentication_methods == (
        frozenset(
            {
                TorAuthenticationMethod.SAFECOOKIE,
            }
        )
    )


def test_protocol_info_allows_missing_tor_version():
    reply = parse_reply(
        "250-PROTOCOLINFO 1",
        "250-AUTH METHODS=SAFECOOKIE",
        "250 OK",
    )

    info = ProtocolInfoParser().parse(
        reply
    )

    assert info.tor_version is None


def test_protocol_info_allows_missing_cookie_file():
    reply = parse_reply(
        "250-PROTOCOLINFO 1",
        "250-AUTH METHODS=HASHEDPASSWORD",
        "250 OK",
    )

    info = ProtocolInfoParser().parse(
        reply
    )

    assert info.cookie_file is None

    assert (
        TorAuthenticationMethod.HASHEDPASSWORD
        in info.authentication_methods
    )


def test_protocol_info_decodes_cookie_path_escapes():
    auth_line = (
        '250-AUTH METHODS=SAFECOOKIE '
        'COOKIEFILE="/tmp/tor\\ control/authcookie"'
    )

    reply = parse_reply(
        "250-PROTOCOLINFO 1",
        auth_line,
        "250 OK",
    )

    info = ProtocolInfoParser().parse(
        reply
    )

    assert info.cookie_file == Path(
        "/tmp/tor control/authcookie"
    )
    


def test_protocol_info_decodes_escaped_quote():
    reply = parse_reply(
        "250-PROTOCOLINFO 1",
        (
            "250-AUTH "
            "METHODS=SAFECOOKIE "
            'COOKIEFILE="/tmp/tor\\"cookie"'
        ),
        "250 OK",
    )

    info = ProtocolInfoParser().parse(
        reply
    )

    assert info.cookie_file == Path(
        '/tmp/tor"cookie'
    )


def test_protocol_info_decodes_tor_version():
    reply = parse_reply(
        "250-PROTOCOLINFO 1",
        "250-AUTH METHODS=SAFECOOKIE",
        '250-VERSION Tor="0.4.8.12"',
        "250 OK",
    )

    info = ProtocolInfoParser().parse(
        reply
    )

    assert info.tor_version == (
        "0.4.8.12"
    )


def test_protocol_info_rejects_error_reply():
    reply = parse_reply(
        "552 Unrecognized command"
    )

    with pytest.raises(
        TorControlProtocolError
    ):
        ProtocolInfoParser().parse(
            reply
        )


def test_protocol_info_requires_protocol_version():
    reply = parse_reply(
        "250-AUTH METHODS=SAFECOOKIE",
        "250 OK",
    )

    with pytest.raises(
        TorControlProtocolError
    ):
        ProtocolInfoParser().parse(
            reply
        )


def test_protocol_info_rejects_invalid_protocol_version():
    reply = parse_reply(
        "250-PROTOCOLINFO one",
        "250 OK",
    )

    with pytest.raises(
        TorControlProtocolError
    ):
        ProtocolInfoParser().parse(
            reply
        )


def test_protocol_info_requires_auth_methods():
    reply = parse_reply(
        "250-PROTOCOLINFO 1",
        '250-AUTH COOKIEFILE="/tmp/cookie"',
        "250 OK",
    )

    with pytest.raises(
        TorControlProtocolError
    ):
        ProtocolInfoParser().parse(
            reply
        )


def test_protocol_info_rejects_unterminated_quote():
    reply = parse_reply(
        "250-PROTOCOLINFO 1",
        (
            "250-AUTH "
            "METHODS=SAFECOOKIE "
            'COOKIEFILE="/tmp/cookie'
        ),
        "250 OK",
    )

    with pytest.raises(
        TorControlProtocolError
    ):
        ProtocolInfoParser().parse(
            reply
        )
