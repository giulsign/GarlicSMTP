# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import tkinter as tk

from garlicsmtp.application import (
    ApplicationViewModel,
    MailboxSummary,
)
from garlicsmtp.gui.tk_mailbox_list_section import (
    MailboxListSection,
)
from tests.support import (
    FakeController,
    make_application_status,
)


def build_section(root):
    controller = FakeController()

    controller.current_status = (
        make_application_status(
            mailboxes=(
                "alice@test.onion",
                "bob@test.onion",
            ),
            mailbox_summaries=(
                MailboxSummary(
                    address="alice@test.onion",
                    message_count=3,
                ),
                MailboxSummary(
                    address="bob@test.onion",
                    message_count=1,
                ),
            ),
        )
    )

    section = MailboxListSection(
        root,
        view_model=ApplicationViewModel(
            controller
        ),
    )

    section.refresh_view()

    return section


def test_mailbox_list_section_displays_mailboxes():
    root = tk.Tk()
    root.withdraw()

    try:
        section = build_section(root)

        assert section.mailbox_list.size() == 2

        assert "alice@test.onion" in (
            section.mailbox_list.get(0)
        )
        assert "3 messages" in (
            section.mailbox_list.get(0)
        )

        assert (
            section.summary_value.cget("text")
            == "2 mailboxes, 4 messages"
        )

    finally:
        root.destroy()


def test_mailbox_list_section_selects_mailbox():
    root = tk.Tk()
    root.withdraw()

    try:
        section = build_section(root)
        selected = []

        section.add_selection_listener(
            selected.append
        )

        assert section.select_mailbox(
            "bob@test.onion"
        )

        assert (
            section.selected_mailbox
            == "bob@test.onion"
        )
        assert selected == [
            "bob@test.onion",
        ]

    finally:
        root.destroy()


def test_mailbox_list_section_preserves_selection():
    root = tk.Tk()
    root.withdraw()

    try:
        section = build_section(root)

        section.select_mailbox(
            "bob@test.onion"
        )

        section.refresh_view()

        assert (
            section.selected_mailbox
            == "bob@test.onion"
        )

    finally:
        root.destroy()


def test_mailbox_list_section_rejects_unknown_selection():
    root = tk.Tk()
    root.withdraw()

    try:
        section = build_section(root)

        assert not section.select_mailbox(
            "missing@test.onion"
        )

    finally:
        root.destroy()


def test_mailbox_list_section_refresh_button_refreshes_view_model():
    root = tk.Tk()
    root.withdraw()

    try:
        section = build_section(root)

        refresh_calls = []

        section.view_model.refresh = (
            lambda: refresh_calls.append(
                "refresh"
            )
        )

        section.refresh_button.invoke()

        assert refresh_calls == [
            "refresh",
        ]

        assert (
            section.mailbox_list.size()
            == 2
        )

    finally:
        root.destroy()