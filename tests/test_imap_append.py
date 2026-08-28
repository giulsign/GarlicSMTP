# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import re
from datetime import timedelta

import pytest

from garlicsmtp.imap.append import (
    IMAPAppendError,
    IMAPAppendParser,
)
from garlicsmtp.imap.append import (
    IMAPAppendItem,
    IMAPAppendRequest,
)



def test_append_parser_detects_append_command():
    assert (
        IMAPAppendParser.is_append_command(
            (
                'A001 APPEND '
                '"archive@test.onion" {12}'
            )
        )
        is True
    )


def test_append_parser_rejects_other_command():
    assert (
        IMAPAppendParser.is_append_command(
            "A001 NOOP"
        )
        is False
    )


def test_append_parser_parses_minimal_request():
    request = IMAPAppendParser.parse(
        (
            'A001 APPEND '
            '"archive@test.onion" {123}'
        )
    )

    assert request.tag == "A001"

    assert request.mailbox == (
        "archive@test.onion"
    )

    assert request.flags == frozenset()

    assert request.internal_date is None

    assert request.literal_size == 123

    assert (
        request.non_synchronizing
        is False
    )


def test_append_parser_parses_atom_mailbox():
    request = IMAPAppendParser.parse(
        "A001 APPEND archive {12}"
    )

    assert request.mailbox == "archive"
    assert request.literal_size == 12


def test_append_parser_unescapes_quoted_mailbox():
    request = IMAPAppendParser.parse(
        (
            'A001 APPEND '
            '"archive \\"special\\"" {12}'
        )
    )

    assert request.mailbox == (
        'archive "special"'
    )


def test_append_parser_parses_system_flags():
    request = IMAPAppendParser.parse(
        (
            'A001 APPEND "archive" '
            r"(\Seen \Flagged \Draft) "
            "{12}"
        )
    )

    assert request.flags == frozenset(
        {
            "\\Seen",
            "\\Flagged",
            "\\Draft",
        }
    )


def test_append_parser_normalizes_system_flags():
    request = IMAPAppendParser.parse(
        (
            'A001 APPEND "archive" '
            r"(\seen \FLAGGED) "
            "{12}"
        )
    )

    assert request.flags == frozenset(
        {
            "\\Seen",
            "\\Flagged",
        }
    )


def test_append_parser_accepts_keyword_flags():
    request = IMAPAppendParser.parse(
        (
            'A001 APPEND "archive" '
            r"(\Seen Important CustomFlag) "
            "{12}"
        )
    )

    assert request.flags == frozenset(
        {
            "\\Seen",
            "Important",
            "CustomFlag",
        }
    )


def test_append_parser_parses_empty_flag_list():
    request = IMAPAppendParser.parse(
        (
            'A001 APPEND "archive" '
            "() {12}"
        )
    )

    assert request.flags == frozenset()


def test_append_parser_parses_internal_date():
    request = IMAPAppendParser.parse(
        (
            'A001 APPEND "archive" '
            '"15-Jul-2026 18:30:45 +0200" '
            "{12}"
        )
    )

    assert request.internal_date is not None

    assert request.internal_date.year == 2026
    assert request.internal_date.month == 7
    assert request.internal_date.day == 15

    assert request.internal_date.hour == 18
    assert request.internal_date.minute == 30
    assert request.internal_date.second == 45

    assert (
        request.internal_date.utcoffset()
        == timedelta(hours=2)
    )


def test_append_parser_parses_flags_and_date():
    request = IMAPAppendParser.parse(
        (
            'A001 APPEND "archive" '
            r"(\Seen \Draft) "
            '"15-Jul-2026 18:30:45 +0200" '
            "{512}"
        )
    )

    assert request.flags == frozenset(
        {
            "\\Seen",
            "\\Draft",
        }
    )

    assert request.internal_date is not None
    assert request.literal_size == 512


def test_append_parser_accepts_non_synchronizing_literal():
    request = IMAPAppendParser.parse(
        (
            'A001 APPEND "archive" '
            "{512+}"
        )
    )

    assert request.literal_size == 512

    assert (
        request.non_synchronizing
        is True
    )

@pytest.mark.parametrize(
    "line, expected",
    [
        (
            'A001 APPEND "archive"',
            "APPEND requires literal size",
        ),
        (
            "A001 APPEND {12}",
            "APPEND requires mailbox",
        ),
        (
            (
                'A001 APPEND "archive" '
                r"(\Recent) {12}"
            ),
            (
                "Unsupported system flag "
                "\\Recent"
            ),
        ),
        (
            (
                'A001 APPEND "archive" '
                '"not a date" {12}'
            ),
            "Invalid APPEND internal date",
        ),
        (
            (
                'A001 APPEND "archive" '
                '"15-Jul-2026 18:30:45" '
                "{12}"
            ),
            (
                "APPEND internal date "
                "requires timezone"
            ),
        ),
        (
            (
                'A001 APPEND "archive" '
                "unexpected {12}"
            ),
            "Invalid APPEND internal date",
        ),
        (
            (
                'A001 APPEND "archive" '
                "() trailing {12}"
            ),
            "Invalid APPEND internal date",
        ),
        (
            (
                'A001 APPEND '
                '"unterminated {12}'
            ),
            "Unterminated quoted string",
        ),
    ],
)
def test_append_parser_rejects_invalid_requests(
    line,
    expected,
):
    with pytest.raises(
        IMAPAppendError,
        match=re.escape(
            expected
        ),
    ):
        IMAPAppendParser.parse(
            line
        )


def test_append_parser_rejects_non_append_command():
    with pytest.raises(
        IMAPAppendError,
        match="Invalid APPEND command",
    ):
        IMAPAppendParser.parse(
            "A001 NOOP"
        )


def test_append_parser_parses_two_items():
    request = IMAPAppendParser.parse(
        (
            'A001 APPEND "archive" '
            '{5} '
            '{7}'
        )
    )

    assert request.tag == "A001"
    assert request.mailbox == "archive"

    assert len(request.items) == 2

    assert (
        request.items[0].literal_size
        == 5
    )

    assert (
        request.items[1].literal_size
        == 7
    )


def test_append_parser_parses_three_items():
    request = IMAPAppendParser.parse(
        (
            'A001 APPEND "archive" '
            '{5} '
            '{7} '
            '{9}'
        )
    )

    assert [
        item.literal_size
        for item in request.items
    ] == [
        5,
        7,
        9,
    ]


def test_append_parser_parses_multiple_items_with_flags():
    request = IMAPAppendParser.parse(
        (
            'A001 APPEND "archive" '
            '(\\Seen) {5} '
            '(\\Flagged custom) {7}'
        )
    )

    assert request.items[0].flags == (
        "\\Seen",
    )

    assert request.items[1].flags == (
        "\\Flagged",
        "custom",
    )


def test_append_parser_parses_multiple_items_with_dates():
    request = IMAPAppendParser.parse(
        (
            'A001 APPEND "archive" '
            '"15-Jul-2026 18:30:45 +0200" '
            '{5} '
            '(\\Seen) '
            '"16-Jul-2026 10:15:00 +0200" '
            '{7}'
        )
    )

    assert len(request.items) == 2

    assert (
        request.items[0]
        .internal_date
        is not None
    )

    assert (
        request.items[0]
        .internal_date
        .day
        == 15
    )

    assert request.items[1].flags == (
        "\\Seen",
    )

    assert (
        request.items[1]
        .internal_date
        is not None
    )

    assert (
        request.items[1]
        .internal_date
        .day
        == 16
    )


def test_append_parser_parses_mixed_literal_modes():
    request = IMAPAppendParser.parse(
        (
            'A001 APPEND "archive" '
            '{5} '
            '{7+} '
            '(\\Seen) {9}'
        )
    )

    assert [
        item.non_synchronizing
        for item in request.items
    ] == [
        False,
        True,
        False,
    ]


def test_append_parser_preserves_single_item_compatibility():
    request = IMAPAppendParser.parse(
        (
            'A001 APPEND "archive" '
            '(\\Seen) '
            '"15-Jul-2026 18:30:45 +0200" '
            '{12+}'
        )
    )

    assert len(request.items) == 1

    assert request.flags == frozenset (
        {"\\Seen"},
    )

    assert (
        request.internal_date
        == request.items[0].internal_date
    )

    assert request.literal_size == 12

    assert (
        request.non_synchronizing
        is True
    )


def test_append_parser_rejects_second_item_without_literal():
    with pytest.raises(
        IMAPAppendError,
        match=(
            "APPEND requires literal size"
        ),
    ):
        IMAPAppendParser.parse(
            (
                'A001 APPEND "archive" '
                '{5} '
                '(\\Seen)'
            )
        )


def test_append_parser_rejects_malformed_second_item():
    with pytest.raises(
        IMAPAppendError,
        match=(
            "Invalid APPEND internal date"
        ),
    ):
        IMAPAppendParser.parse(
            (
                'A001 APPEND "archive" '
                '{5} '
                'unexpected {7}'
            )
        )