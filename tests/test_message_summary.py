# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from datetime import UTC, datetime

import pytest

from garlicsmtp.application import (
    MessageSummary,
)


def make_summary(
    *,
    flags=(),
):
    return MessageSummary(
        id="message-1",
        uid=7,
        sender="alice@test.onion",
        subject="GarlicSMTP",
        internal_date=datetime(
            2026,
            8,
            6,
            9,
            30,
            tzinfo=UTC,
        ),
        size=128,
        flags=tuple(flags),
    )


def test_message_summary_exposes_flags():
    summary = make_summary(
        flags=(
            "\\Seen",
            "\\Flagged",
        )
    )

    assert summary.seen is True
    assert summary.flagged is True
    assert summary.deleted is False
    assert summary.draft is False


def test_message_summary_rejects_empty_id():
    with pytest.raises(
        ValueError
    ):
        MessageSummary(
            id="",
            uid=1,
            sender="alice@test.onion",
            subject="Test",
            internal_date=datetime.now(
                UTC
            ),
            size=1,
            flags=(),
        )


def test_message_summary_rejects_invalid_uid():
    with pytest.raises(
        ValueError
    ):
        MessageSummary(
            id="message-1",
            uid=0,
            sender="alice@test.onion",
            subject="Test",
            internal_date=datetime.now(
                UTC
            ),
            size=1,
            flags=(),
        )


def test_message_summary_rejects_negative_size():
    with pytest.raises(
        ValueError
    ):
        MessageSummary(
            id="message-1",
            uid=1,
            sender="alice@test.onion",
            subject="Test",
            internal_date=datetime.now(
                UTC
            ),
            size=-1,
            flags=(),
        )

