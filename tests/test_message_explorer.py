# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from datetime import UTC, datetime

import pytest

from garlicsmtp.application import (
    MessageExplorerService,
)
from garlicsmtp.models import (
    Envelope,
    MailHeaders,
    MailMessage,
)
from garlicsmtp.storage.store import (
    MessageStore,
)


def make_message(
    *,
    sender="alice@test.onion",
    header_sender=None,
    subject="Test subject",
    body="Hello",   
):
    headers = MailHeaders()

    if header_sender is not None:
        headers.add(
            "From",
            header_sender,
        )

    if subject is not None:
        headers.add(
            "Subject",
            subject,
        )

    return MailMessage(
        envelope=Envelope(
            sender=sender,
            recipients=[
                "bob@test.onion",
            ],
        ),
        headers=headers,
        body=body,
    )


def test_message_explorer_lists_messages():
    store = MessageStore()

    first = store.append_entry(
        "bob@test.onion",
        make_message(
            subject="First"
        ),
        flags={
            "\\Seen",
        },
        internal_date=datetime(
            2026,
            8,
            5,
            10,
            0,
            tzinfo=UTC,
        ),
    )

    second = store.append_entry(
        "bob@test.onion",
        make_message(
            subject="Second",
            header_sender=(
                "Alice <alice@test.onion>"
            ),
        ),
        flags={
            "\\Flagged",
        },
        internal_date=datetime(
            2026,
            8,
            6,
            10,
            0,
            tzinfo=UTC,
        ),
    )

    explorer = MessageExplorerService(
        store
    )

    summaries = explorer.list_messages(
        "bob@test.onion"
    )

    assert [
        summary.id
        for summary in summaries
    ] == [
        second.id,
        first.id,
    ]

    assert summaries[0].uid == second.uid
    assert summaries[0].subject == "Second"

    assert summaries[0].sender == (
        "Alice <alice@test.onion>"
    )

    assert summaries[0].size > 0
    assert summaries[0].flagged is True

    assert summaries[1].subject == "First"
    assert summaries[1].seen is True


def test_message_explorer_uses_envelope_sender():
    store = MessageStore()

    entry = store.save_entry(
        "bob@test.onion",
        make_message(
            sender="alice@test.onion",
            header_sender=None,
        ),
    )

    summary = (
        MessageExplorerService(
            store
        )
        .get_summary(
            "bob@test.onion",
            entry.id,
        )
    )

    assert summary is not None

    assert summary.sender == (
        "alice@test.onion"
    )


def test_message_explorer_uses_subject_fallback():
    store = MessageStore()

    entry = store.save_entry(
        "bob@test.onion",
        make_message(
            subject=None
        ),
    )

    summary = (
        MessageExplorerService(
            store
        )
        .get_summary(
            "bob@test.onion",
            entry.id,
        )
    )

    assert summary is not None
    assert summary.subject == (
        "(No subject)"
    )


def test_message_explorer_calculates_size():
    store = MessageStore()

    entry = store.save_entry(
        "bob@test.onion",
        make_message(
            subject="Size test",
            body="Hello",
        ),
    )

    summary = (
        MessageExplorerService(
            store
        )
        .get_summary(
            "bob@test.onion",
            entry.id,
        )
    )

    assert summary is not None
    assert summary.size > 0


def test_message_explorer_returns_entry():
    store = MessageStore()

    entry = store.save_entry(
        "bob@test.onion",
        make_message()
    )

    restored = (
        MessageExplorerService(
            store
        )
        .get_message(
            "bob@test.onion",
            entry.id,
        )
    )

    assert restored is not None
    assert restored.id == entry.id


def test_message_explorer_returns_none_for_unknown_message():
    explorer = MessageExplorerService(
        MessageStore()
    )

    assert explorer.get_summary(
        "bob@test.onion",
        "missing",
    ) is None


@pytest.mark.parametrize(
    "mailbox",
    [
        "",
        "   ",
    ],
)
def test_message_explorer_rejects_empty_mailbox(
    mailbox,
):
    explorer = MessageExplorerService(
        MessageStore()
    )

    with pytest.raises(
        ValueError
    ):
        explorer.list_messages(
            mailbox
        )


def test_message_explorer_rejects_empty_message_id():
    explorer = MessageExplorerService(
        MessageStore()
    )

    with pytest.raises(
        ValueError
    ):
        explorer.get_message(
            "bob@test.onion",
            " ",
        )


def test_message_explorer_marks_message_as_read():
    store = MessageStore()

    entry = store.save_entry(
        "bob@test.onion",
        make_message(),
    )

    explorer = MessageExplorerService(
        store
    )

    explorer.mark_read(
        "bob@test.onion",
        entry.id,
    )

    restored = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert restored is not None
    assert "\\Seen" in restored.flags


def test_message_explorer_marks_message_as_unread():
    store = MessageStore()

    entry = store.append_entry(
        "bob@test.onion",
        make_message(),
        flags={
            "\\Seen",
        },
        internal_date=datetime(
            2026,
            8,
            6,
            10,
            0,
            tzinfo=UTC,
        ),
    )

    explorer = MessageExplorerService(
        store
    )

    explorer.mark_unread(
        "bob@test.onion",
        entry.id,
    )

    restored = store.get_entry(
        "bob@test.onion",
        entry.id,
    )

    assert restored is not None
    assert "\\Seen" not in restored.flags


def test_message_explorer_deletes_message():
    store = MessageStore()

    entry = store.save_entry(
        "bob@test.onion",
        make_message(),
    )

    explorer = MessageExplorerService(
        store
    )

    result = explorer.delete_message(
        "bob@test.onion",
        entry.id,
    )

    assert result is True

    assert store.get_entry(
        "bob@test.onion",
        entry.id,
    ) is None
