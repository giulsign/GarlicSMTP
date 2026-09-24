# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from datetime import UTC, datetime

import pytest

from garlicsmtp.application import (
    MessageFormatter,
    MessageSummary,
)


def make_summary(
    *,
    sender="alice@test.onion",
    subject="GarlicSMTP",
    internal_date=None,
    size=128,
    flags=(),
):
    return MessageSummary(
        id="message-1",
        uid=7,
        sender=sender,
        subject=subject,
        internal_date=(
            internal_date
            or datetime(
                2026,
                8,
                6,
                10,
                30,
                tzinfo=UTC,
            )
        ),
        size=size,
        flags=tuple(flags),
    )


def fixed_now():
    return datetime(
        2026,
        8,
        6,
        12,
        0,
        tzinfo=UTC,
    )


def test_message_formatter_formats_unread_status():
    formatter = MessageFormatter(
        now_provider=fixed_now
    )

    assert formatter.format_status(
        make_summary()
    ) == "●"


def test_message_formatter_formats_seen_status():
    formatter = MessageFormatter(
        now_provider=fixed_now
    )

    assert formatter.format_status(
        make_summary(
            flags=(
                "\\Seen",
            )
        )
    ) == "✓"


def test_message_formatter_formats_multiple_flags():
    formatter = MessageFormatter(
        now_provider=fixed_now
    )

    assert formatter.format_status(
        make_summary(
            flags=(
                "\\Flagged",
                "\\Draft",
                "\\Deleted",
            )
        )
    ) == "● ⚑ ✎ ⌫"


def test_message_formatter_formats_today():
    formatter = MessageFormatter(
        now_provider=fixed_now
    )

    value = datetime(
        2026,
        8,
        6,
        10,
        30,
        tzinfo=UTC,
    )

    assert formatter.format_date(
        value
    ) == "Today 12:30" or (
        formatter.format_date(value)
        == "Today 10:30"
    )


def test_message_formatter_formats_today():
    now = datetime.now(
        UTC
    )

    formatter = MessageFormatter(
        now_provider=lambda: now
    )

    assert formatter.format_date(
        now
    ).startswith(
        "Today "
    )


def test_message_formatter_formats_yesterday():
    now = datetime(
        2026,
        8,
        6,
        12,
        0,
        tzinfo=UTC,
    )

    value = datetime(
        2026,
        8,
        5,
        10,
        30,
        tzinfo=UTC,
    )

    formatter = MessageFormatter(
        now_provider=lambda: now
    )

    assert formatter.format_date(
        value
    ).startswith(
        "Yesterday "
    )


@pytest.mark.parametrize(
    ("size", "expected"),
    [
        (0, "0 B"),
        (512, "512 B"),
        (1024, "1.0 KB"),
        (2048, "2.0 KB"),
        (1024 * 1024, "1.0 MB"),
        (
            1024 * 1024 * 1024,
            "1.0 GB",
        ),
    ],
)
def test_message_formatter_formats_size(
    size,
    expected,
):
    assert (
        MessageFormatter()
        .format_size(
            size
        )
        == expected
    )


def test_message_formatter_formats_sender_fallback():
    formatter = MessageFormatter()

    assert formatter.format_sender(
        make_summary(
            sender=" "
        )
    ) == "(Unknown sender)"


def test_message_formatter_formats_subject_fallback():
    formatter = MessageFormatter()

    assert formatter.format_subject(
        make_summary(
            subject=" "
        )
    ) == "(No subject)"


def test_message_formatter_builds_tooltip():
    formatter = MessageFormatter(
        now_provider=fixed_now
    )

    tooltip = formatter.build_tooltip(
        make_summary(
            flags=(
                "\\Seen",
                "\\Flagged",
            ),
            size=2048,
        )
    )

    assert "UID: 7" in tooltip
    assert "From: alice@test.onion" in tooltip
    assert "Subject: GarlicSMTP" in tooltip
    assert "\\Seen" in tooltip
    assert "2048 bytes" in tooltip


def test_message_formatter_rejects_negative_size():
    with pytest.raises(
        ValueError
    ):
        MessageFormatter().format_size(
            -1
        )
