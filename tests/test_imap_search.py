# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import pytest

from garlicsmtp.imap import (
    IMAPSearchEngine,
    IMAPSearchError,
)
from garlicsmtp.storage.entry import MessageEntry
from copy import deepcopy


def build_entry(
    message,
    uid: int,
    flags: set[str] | None = None,
) -> MessageEntry:
    return MessageEntry(
        id=f"message-{uid}",
        mailbox="bob@test.onion",
        uid=uid,
        message=deepcopy(message),
        flags=set(flags or set()),
    )


def test_imap_search_all(
    message,
):
    engine = IMAPSearchEngine(
        entries=[
            build_entry(message, 1),
            build_entry(message, 2),
        ]
    )

    assert engine.search(
        ["ALL"]
    ) == [1, 2]


def test_imap_search_seen(
    message,
):
    engine = IMAPSearchEngine(
        entries=[
            build_entry(
                message,
                1,
                {
                    "\\Seen",
                },
            ),
            build_entry(
                message,
                2,
            ),
        ]
    )

    assert engine.search(
        ["SEEN"]
    ) == [1]


def test_imap_search_unseen(
    message,
):
    engine = IMAPSearchEngine(
        entries=[
            build_entry(
                message,
                1,
                {
                    "\\Seen",
                },
            ),
            build_entry(
                message,
                2,
            ),
        ]
    )

    assert engine.search(
        ["UNSEEN"]
    ) == [2]


def test_imap_search_flagged(
    message,
):
    engine = IMAPSearchEngine(
        entries=[
            build_entry(
                message,
                1,
                {
                    "\\Flagged",
                },
            ),
            build_entry(
                message,
                2,
            ),
        ]
    )

    assert engine.search(
        ["FLAGGED"]
    ) == [1]


def test_imap_search_combines_criteria(
    message,
):
    engine = IMAPSearchEngine(
        entries=[
            build_entry(
                message,
                1,
                {
                    "\\Seen",
                    "\\Flagged",
                },
            ),
            build_entry(
                message,
                2,
                {
                    "\\Seen",
                },
            ),
            build_entry(
                message,
                3,
                {
                    "\\Flagged",
                },
            ),
        ]
    )

    assert engine.search(
        [
            "SEEN",
            "FLAGGED",
        ]
    ) == [1]


def test_imap_search_rejects_unsupported_criterion(
    message,
):
    engine = IMAPSearchEngine(
        entries=[
            build_entry(
                message,
                1,
            ),
        ]
    )

    with pytest.raises(
        IMAPSearchError,
        match=(
            "Unsupported SEARCH criterion "
            "LARGER"
        ),
    ):
        engine.search(
            [
                "LARGER",
            ]
        )


def test_imap_search_from(
    message,
):
    first = build_entry(
        message,
        1,
    )

    second = build_entry(
        message,
        2,
    )

    first.message.envelope.sender = (
        "alice@test.onion"
    )

    second.message.envelope.sender = (
        "carol@test.onion"
    )

    engine = IMAPSearchEngine(
        entries=[
            first,
            second,
        ]
    )

    assert engine.search(
        [
            "FROM",
            "alice",
        ]
    ) == [1]


def test_imap_search_to(
    message,
):
    first = build_entry(
        message,
        1,
    )

    second = build_entry(
        message,
        2,
    )

    first.message.envelope.recipients = [
        "bob@test.onion"
    ]

    second.message.envelope.recipients = [
        "dave@test.onion"
    ]

    engine = IMAPSearchEngine(
        entries=[
            first,
            second,
        ]
    )

    assert engine.search(
        [
            "TO",
            "bob",
        ]
    ) == [1]


def test_imap_search_subject(
    message,
):
    first = build_entry(
        message,
        1,
    )

    second = build_entry(
        message,
        2,
    )

    first.message.headers.fields[
        "Subject"
    ] = "GarlicSMTP release"

    second.message.headers.fields[
        "Subject"
    ] = "Unrelated message"

    engine = IMAPSearchEngine(
        entries=[
            first,
            second,
        ]
    )

    assert engine.search(
        [
            "SUBJECT",
            "garlicsmtp",
        ]
    ) == [1]


def test_imap_search_text(
    message,
):
    first = build_entry(
        message,
        1,
    )

    second = build_entry(
        message,
        2,
    )

    first.message.body = (
        "The hidden service is ready"
    )

    second.message.body = (
        "Nothing relevant"
    )

    engine = IMAPSearchEngine(
        entries=[
            first,
            second,
        ]
    )

    assert engine.search(
        [
            "TEXT",
            "hidden service",
        ]
    ) == [1]


def test_imap_search_combines_text_and_flags(
    message,
):
    first = build_entry(
        message,
        1,
        {
            "\\Seen",
        },
    )

    second = build_entry(
        message,
        2,
    )

    first.message.headers.fields[
        "Subject"
    ] = "Tor status"

    second.message.headers.fields[
        "Subject"
    ] = "Tor status"

    engine = IMAPSearchEngine(
        entries=[
            first,
            second,
        ]
    )

    assert engine.search(
        [
            "SEEN",
            "SUBJECT",
            "tor",
        ]
    ) == [1]


def test_imap_search_rejects_missing_value(
    message,
):
    engine = IMAPSearchEngine(
        entries=[
            build_entry(
                message,
                1,
            ),
        ]
    )

    with pytest.raises(
        IMAPSearchError,
        match=(
            "SUBJECT requires a value"
        ),
    ):
        engine.search(
            [
                "SUBJECT",
            ]
        )