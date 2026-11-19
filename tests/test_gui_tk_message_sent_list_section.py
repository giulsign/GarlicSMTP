# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import tkinter as tk
from datetime import UTC, datetime

from garlicsmtp.application import MessageSummary
from garlicsmtp.gui.tk_message_sent_list_section import (
    MessageSentListSection,
)


def test_sent_list_displays_saved_recipient_name():
    root = tk.Tk()
    root.withdraw()

    try:
        message = MessageSummary(
            id="message-1",
            uid=1,
            sender="alice@example.onion",
            recipient="mario@example.onion",
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
            def format_contact_address(
                self,
                onion_address,
            ):
                if onion_address == "mario@example.onion":
                    return "Mario Rossi — mario@example.onion"
                return onion_address

        section = MessageSentListSection(
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
            values[section.COLUMN_RECIPIENT]
            == "Mario Rossi — mario@example.onion"
        )

        assert message.sender == "alice@example.onion"
        assert message.recipient == "mario@example.onion"

    finally:
        root.destroy()


def test_sent_list_uses_to_column_heading():
    root = tk.Tk()
    root.withdraw()

    try:
        class FakeMessageListViewModel:
            messages = ()
            selected_message_id = None

        section = MessageSentListSection(
            root,
            view_model=FakeMessageListViewModel(),
        )

        assert section.COLUMN_RECIPIENT == 2
        assert section.COLUMNS[section.COLUMN_RECIPIENT] == "recipient"

        assert (
            section.table.heading(
                "recipient",
                "text",
            )
            == "To"
        )

    finally:
        root.destroy()