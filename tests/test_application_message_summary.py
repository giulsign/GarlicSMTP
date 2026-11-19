# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from datetime import UTC, datetime

from garlicsmtp.application.message_summary import MessageSummary


def test_message_summary_accepts_optional_recipient():
    summary = MessageSummary(
        id="message-1",
        uid=1,
        sender="alice@example.onion",
        subject="Test",
        internal_date=datetime(
            2026, 8, 6, 10, 0, tzinfo=UTC
        ),
        size=128,
        flags=(),
        recipient="mario@example.onion",
    )

    assert summary.recipient == "mario@example.onion"
    assert summary.sender == "alice@example.onion"
