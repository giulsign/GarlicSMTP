# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import tkinter as tk
from datetime import UTC, datetime
from tkinter import messagebox

from garlicsmtp.application import (
    MessageListViewModel,
    MessageSummary,
)
from garlicsmtp.gui.tk_message_list_section import (
    MessageListSection,
)


def make_summary(
    *,
    message_id: str,
    uid: int,
    subject: str,
    flags=(),
    size=128,
):
    return MessageSummary(
        id=message_id,
        uid=uid,
        sender="alice@test.onion",
        subject=subject,
        internal_date=datetime(
            2026,
            8,
            6,
            10,
            uid,
            tzinfo=UTC,
        ),
        size=size,
        flags=tuple(flags),
    )


class FakeExplorer:

    def __init__(self):
        self.messages = (
            make_summary(
                message_id="message-1",
                uid=1,
                subject="Unread",
                flags=(),
            ),
            make_summary(
                message_id="message-2",
                uid=2,
                subject="Flagged",
                flags=(
                    "\\Seen",
                    "\\Flagged",
                ),
                size=2048,
            ),
        )

    def list_messages(
        self,
        mailbox,
    ):
        del mailbox
        return self.messages


def build_section():
    root = tk.Tk()
    root.withdraw()

    view_model = MessageListViewModel(
        FakeExplorer()
    )
    view_model.select_mailbox(
        "bob@test.onion"
    )

    section = MessageListSection(
        root,
        view_model=view_model,
    )
    section.refresh_view()

    return root, section, view_model


def test_message_list_section_displays_messages():
    root, section, _ = build_section()

    try:
        rows = section.table.get_children()

        assert len(rows) == 2

        first = section.table.item(
            rows[0],
            "values",
        )
        second = section.table.item(
            rows[1],
            "values",
        )

        assert (
            first[
                section.COLUMN_SUBJECT
            ]
            == "Unread"
        )

        assert (
            second[
                section.COLUMN_SIZE
            ]
            == "2.0 KB"
        )

    finally:
        root.destroy()


def test_message_list_section_displays_flags():
    root, section, _ = build_section()

    try:
        rows = section.table.get_children()

        first = section.table.item(
            rows[0],
            "values",
        )
        second = section.table.item(
            rows[1],
            "values",
        )

        assert (
            "●"
            in first[
                section.COLUMN_STATUS
            ]
        )

        assert (
            "⚑"
            in second[
                section.COLUMN_STATUS
            ]
        )

    finally:
        root.destroy()


def test_message_list_section_selects_message():
    root, section, view_model = (
        build_section()
    )

    try:
        selected = []

        section.add_selection_listener(
            selected.append
        )

        assert section.select_message(
            "message-2"
        ) is True

        assert (
            section.selected_message_id
            == "message-2"
        )

        assert (
            view_model.selected_message_id
            == "message-2"
        )

        assert selected == [
            "message-2",
        ]

    finally:
        root.destroy()


def test_message_list_section_rejects_unknown_message():
    root, section, view_model = (
        build_section()
    )

    try:
        assert section.select_message(
            "missing"
        ) is False

        assert (
            section.selected_message_id
            is None
        )

        assert (
            view_model.selected_message_id
            is None
        )

    finally:
        root.destroy()


def test_message_list_section_preserves_selection():
    root, section, view_model = (
        build_section()
    )

    try:
        assert section.select_message(
            "message-1"
        ) is True

        section.refresh_view()

        assert (
            section.selected_message_id
            == "message-1"
        )

        assert (
            view_model.selected_message_id
            == "message-1"
        )

    finally:
        root.destroy()


def test_message_list_section_tree_selection_updates_view_model():
    root, section, view_model = (
        build_section()
    )

    try:
        selected = []

        section.add_selection_listener(
            selected.append
        )

        section.table.selection_set(
            "message-2"
        )
        section.table.focus(
            "message-2"
        )
        section.table.event_generate(
            "<<TreeviewSelect>>"
        )

        root.update()

        assert (
            section.selected_message_id
            == "message-2"
        )

        assert (
            view_model.selected_message_id
            == "message-2"
        )

        assert selected == [
            "message-2",
        ]

    finally:
        root.destroy()


def test_message_list_section_selection_change_updates_view_model():
    root, section, view_model = (
        build_section()
    )

    try:
        selected = []

        section.add_selection_listener(
            selected.append
        )

        assert section.select_message(
            "message-1"
        ) is True

        selected.clear()

        section.table.selection_set(
            "message-2"
        )
        section.table.focus(
            "message-2"
        )
        section.table.event_generate(
            "<<TreeviewSelect>>"
        )

        root.update()

        assert (
            section.selected_message_id
            == "message-2"
        )

        assert (
            view_model.selected_message_id
            == "message-2"
        )

        assert selected == [
            "message-2",
        ]

    finally:
        root.destroy()


def test_message_list_section_refresh_button_updates_messages():
    root = tk.Tk()
    root.withdraw()

    try:
        class MutableExplorer:

            def __init__(self):
                self.messages = (
                    make_summary(
                        message_id="message-1",
                        uid=1,
                        subject="First",
                    ),
                )

            def list_messages(
                self,
                mailbox,
            ):
                del mailbox
                return self.messages

        explorer = MutableExplorer()

        view_model = MessageListViewModel(
            explorer
        )
        view_model.select_mailbox(
            "bob@test.onion"
        )

        section = MessageListSection(
            root,
            view_model=view_model,
        )
        section.refresh_view()

        assert len(
            section.table.get_children()
        ) == 1

        explorer.messages = (
            make_summary(
                message_id="message-1",
                uid=1,
                subject="First",
            ),
            make_summary(
                message_id="message-2",
                uid=2,
                subject="Second",
            ),
        )

        section.refresh_button.invoke()

        rows = (
            section.table.get_children()
        )

        assert len(rows) == 2

        second = section.table.item(
            rows[1],
            "values",
        )

        assert (
            second[
                section.COLUMN_SUBJECT
            ]
            == "Second"
        )

    finally:
        root.destroy()


def test_message_list_section_mark_read_button_marks_selected_message():
    root, section, view_model = (
        build_section()
    )

    try:
        assert section.select_message(
            "message-1"
        ) is True

        calls = []

        view_model.mark_selected_read = (
            lambda: calls.append(
                "mark_read"
            ) or True
        )

        section.mark_read_button.invoke()

        assert calls == [
            "mark_read",
        ]

    finally:
        root.destroy()


def test_message_list_section_mark_unread_button_marks_selected_message():
    root, section, view_model = (
        build_section()
    )

    try:
        assert section.select_message(
            "message-2"
        ) is True

        calls = []

        view_model.mark_selected_unread = (
            lambda: calls.append(
                "mark_unread"
            ) or True
        )

        section.mark_unread_button.invoke()

        assert calls == [
            "mark_unread",
        ]

    finally:
        root.destroy()


def test_message_list_section_delete_requires_confirmation(
    monkeypatch,
):
    root, section, view_model = (
        build_section()
    )

    try:
        assert section.select_message(
            "message-1"
        ) is True

        calls = []

        view_model.delete_selected = (
            lambda: calls.append(
                "delete"
            ) or True
        )

        monkeypatch.setattr(
            messagebox,
            "askyesno",
            lambda *args, **kwargs: False,
        )

        section.delete_button.invoke()

        assert calls == []

    finally:
        root.destroy()


def test_message_list_section_delete_confirms_selected_message(
    monkeypatch,
):
    root, section, view_model = (
        build_section()
    )

    try:
        assert section.select_message(
            "message-1"
        ) is True

        calls = []

        view_model.delete_selected = (
            lambda: calls.append(
                "delete"
            ) or True
        )

        monkeypatch.setattr(
            messagebox,
            "askyesno",
            lambda *args, **kwargs: True,
        )

        section.delete_button.invoke()

        assert calls == [
            "delete",
        ]

    finally:
        root.destroy()


def test_message_list_section_delete_without_selection_does_nothing(
    monkeypatch,
):
    root, section, view_model = (
        build_section()
    )

    try:
        dialog_calls = []
        delete_calls = []

        view_model.delete_selected = (
            lambda: delete_calls.append(
                "delete"
            ) or True
        )

        monkeypatch.setattr(
            messagebox,
            "askyesno",
            lambda *args, **kwargs: (
                dialog_calls.append(
                    "dialog"
                )
                or True
            ),
        )

        section.delete_button.invoke()

        assert dialog_calls == []
        assert delete_calls == []

    finally:
        root.destroy()


def test_message_list_section_notifies_deleted_message(
    monkeypatch,
):
    root, section, view_model = (
        build_section()
    )

    try:
        assert section.select_message(
            "message-1"
        ) is True

        deleted = []

        section.add_deleted_listener(
            deleted.append
        )

        view_model.delete_selected = (
            lambda: True
        )

        monkeypatch.setattr(
            messagebox,
            "askyesno",
            lambda *args, **kwargs: True,
        )

        section.delete_button.invoke()

        assert deleted == [
            "message-1",
        ]

    finally:
        root.destroy()


def test_message_list_table_uses_garlic_style():
    root, section, _ = build_section()

    try:
        assert (
            section.table.cget("style")
            == "Garlic.Treeview"
        )

    finally:
        root.destroy()


def test_message_list_section_tags_unread_messages():
    root, section, _ = build_section()

    try:
        unread = section.table.item(
            "message-1",
            "tags",
        )

        read = section.table.item(
            "message-2",
            "tags",
        )

        assert "unread" in unread
        assert "unread" not in read

    finally:
        root.destroy()


def test_message_list_section_has_compact_requested_width():
    root, section, _ = build_section()

    try:
        section.grid(
            row=0,
            column=0,
            sticky="nsew",
        )
        root.update_idletasks()

        assert section.winfo_reqwidth() <= 600

    finally:
        root.destroy()