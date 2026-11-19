# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import tkinter as tk
from datetime import UTC, datetime

from garlicsmtp.application import MessageSummary
from garlicsmtp.gui.tk_message_received_list_section import (
    MessageReceivedListSection,
)


def test_received_list_displays_saved_contact_name():
    root = tk.Tk()
    root.withdraw()

    try:
        message = MessageSummary(
            id="message-1",
            uid=1,
            sender="mario@example.onion",
            subject="Test",
            internal_date=datetime(
                2026, 8, 6, 10, 0, tzinfo=UTC
            ),
            size=128,
            flags=(),
        )

        class FakeMessageListViewModel:
            messages = (message,)
            selected_message_id = None

        class FakeContactsViewModel:
            def format_contact_address(self, onion_address):
                if onion_address == "mario@example.onion":
                    return "Mario Rossi — mario@example.onion"
                return onion_address

        section = MessageReceivedListSection(
            root,
            view_model=FakeMessageListViewModel(),
            contacts_view_model=FakeContactsViewModel(),
        )

        section.refresh_view()

        values = section.table.item(
            "message-1",
            "values",
        )

        assert (
            values[section.COLUMN_SENDER]
            == "Mario Rossi — mario@example.onion"
        )

        assert message.sender == "mario@example.onion"

    finally:
        root.destroy()


def test_received_list_preserves_unknown_sender():
    root = tk.Tk()
    root.withdraw()

    try:
        message = MessageSummary(
            id="message-2",
            uid=2,
            sender="unknown@example.onion",
            subject="Test",
            internal_date=datetime(
                2026, 8, 6, 10, 0, tzinfo=UTC
            ),
            size=128,
            flags=(),
        )

        class FakeMessageListViewModel:
            messages = (message,)
            selected_message_id = None

        class FakeContactsViewModel:
            def format_contact_address(self, onion_address):
                if onion_address == "mario@example.onion":
                    return "Mario Rossi — mario@example.onion"
                return onion_address

        section = MessageReceivedListSection(
            root,
            view_model=FakeMessageListViewModel(),
            contacts_view_model=FakeContactsViewModel(),
        )

        section.refresh_view()

        values = section.table.item(
            "message-2",
            "values",
        )

        assert (
            values[section.COLUMN_SENDER]
            == "unknown@example.onion"
        )

        assert message.sender == "unknown@example.onion"

    finally:
        root.destroy()