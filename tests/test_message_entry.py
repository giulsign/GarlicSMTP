# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from datetime import UTC

from garlicsmtp.storage.entry import MessageEntry


def test_message_entry_defaults(message):

    entry = MessageEntry(
        id="message-id",
        mailbox="bob@test.onion",
        uid=1,
        message=message,
    )

    assert entry.id == "message-id"
    assert entry.mailbox == "bob@test.onion"
    assert entry.uid == 1
    assert entry.message is message

    assert entry.internal_date.tzinfo == UTC
    assert entry.flags == set()


def test_message_entry_flags_are_not_shared(message):

    first = MessageEntry(
        id="first",
        mailbox="bob@test.onion",
        uid=1,
        message=message,
    )

    second = MessageEntry(
        id="second",
        mailbox="bob@test.onion",
        uid=2,
        message=message,
    )

    first.flags.add("\\Seen")

    assert first.flags == {
        "\\Seen",
    }

    assert second.flags == set()