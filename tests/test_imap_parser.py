# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import pytest

from garlicsmtp.imap import (
    IMAPParseError,
    IMAPParser,
)


def test_imap_parser_parses_command():

    command = IMAPParser.parse(
        "A001 CAPABILITY\r\n"
    )

    assert command.tag == "A001"
    assert command.name == "CAPABILITY"
    assert command.arguments == []


def test_imap_parser_parses_arguments():

    command = IMAPParser.parse(
        "A002 LOGIN alice secret\r\n"
    )

    assert command.tag == "A002"
    assert command.name == "LOGIN"
    assert command.arguments == [
        "alice",
        "secret",
    ]


def test_imap_parser_normalizes_command_name():

    command = IMAPParser.parse(
        "A003 noop"
    )

    assert command.name == "NOOP"


@pytest.mark.parametrize(
    "line",
    [
        "",
        "A001",
        "* CAPABILITY",
    ],
)
def test_imap_parser_rejects_invalid_commands(
    line,
):

    with pytest.raises(
        IMAPParseError
    ):
        IMAPParser.parse(line)


def test_imap_parser_preserves_quoted_argument():

    command = IMAPParser.parse(
        (
            'A003 UID SEARCH '
            'TEXT "over Tor"'
        )
    )

    assert command.tag == "A003"
    assert command.name == "UID"
    assert command.arguments == [
        "SEARCH",
        "TEXT",
        "over Tor",
    ]


def test_imap_parser_rejects_unclosed_quote():

    with pytest.raises(
        IMAPParseError,
        match="Invalid IMAP command",
    ):
        IMAPParser.parse(
            'A001 LOGIN alice "secret'
        )


def test_imap_parser_preserves_system_flags():

    command = IMAPParser.parse(
        (
            "A003 UID STORE 1 "
            "+FLAGS (\\Seen \\Flagged)"
        )
    )

    assert command.arguments == [
        "STORE",
        "1",
        "+FLAGS",
        "(\\Seen",
        "\\Flagged)",
    ]


def test_imap_parser_preserves_quotes_and_backslashes():

    command = IMAPParser.parse(
        (
            'A003 UID SEARCH '
            'TEXT "over \\ Tor"'
        )
    )

    assert command.arguments == [
        "SEARCH",
        "TEXT",
        "over \\ Tor",
    ]