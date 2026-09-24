# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.imap.idle import (
    IMAPIdleSession,
)
from garlicsmtp.imap.store_event_adapter import (
    IMAPStoreEventAdapter,
)


def test_store_event_adapter_notifies_selected_mailbox():
    idle = IMAPIdleSession()

    adapter = IMAPStoreEventAdapter(
        notification_sink=idle,
        selected_mailbox=(
            lambda: "bob@test.onion"
        ),
        mailbox_count=(
            lambda mailbox: 3
        ),
    )

    adapter.message_added(
        "bob@test.onion"
    )

    assert idle.drain_notifications() == (
        "* 3 EXISTS",
    )


def test_store_event_adapter_ignores_other_mailbox():
    idle = IMAPIdleSession()

    adapter = IMAPStoreEventAdapter(
        notification_sink=idle,
        selected_mailbox=(
            lambda: "bob@test.onion"
        ),
        mailbox_count=(
            lambda mailbox: 3
        ),
    )

    adapter.message_added(
        "alice@test.onion"
    )

    assert idle.has_notifications() is False


def test_store_event_adapter_notifies_expunge():
    idle = IMAPIdleSession()

    adapter = IMAPStoreEventAdapter(
        notification_sink=idle,
        selected_mailbox=(
            lambda: "bob@test.onion"
        ),
        mailbox_count=(
            lambda mailbox: 2
        ),
    )

    adapter.message_removed(
        "bob@test.onion",
        2,
    )

    assert idle.drain_notifications() == (
        "* 2 EXPUNGE",
    )
