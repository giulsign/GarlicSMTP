# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import tkinter as tk
from tkinter import ttk
from datetime import UTC, datetime

from garlicsmtp.application import (
    MessagePreviewViewModel,
)
from garlicsmtp.gui.tk_message_preview_section import (
    MessagePreviewSection,
)
from garlicsmtp.models import (
    Envelope,
    MailHeaders,
    MailMessage,
)
from garlicsmtp.storage.entry import (
    MessageEntry,
)


class FakeExplorer:

    def get_message(
        self,
        mailbox,
        message_id,
    ):
        del mailbox
        del message_id
        return None

def make_entry():
    headers = MailHeaders()

    headers.add(
        "From",
        "Alice <alice@test.onion>",
    )
    headers.add(
        "Subject",
        "GarlicSMTP Preview",
    )

    return MessageEntry(
        id="message-1",
        mailbox="bob@test.onion",
        uid=12,
        message=MailMessage(
            envelope=Envelope(
                sender="alice@test.onion",
                recipients=[
                    "bob@test.onion",
                ],
            ),
            headers=headers,
            body="Hello from GarlicSMTP",
        ),
        internal_date=datetime(
            2026,
            8,
            7,
            9,
            30,
            tzinfo=UTC,
        ),
        flags={
            "\\Seen",
            "\\Flagged",
        },
    )


class MessageExplorer:

    def get_message(
        self,
        mailbox,
        message_id,
    ):
        if (
            mailbox
            == "bob@test.onion"
            and message_id
            == "message-1"
        ):
            return make_entry()

        return None

def test_message_preview_section_starts_empty():
    root = tk.Tk()
    root.withdraw()

    try:
        view_model = (
            MessagePreviewViewModel(
                FakeExplorer()
            )
        )

        section = MessagePreviewSection(
            root,
            view_model=view_model,
        )

        assert (
            section.placeholder_value.cget(
                "text"
            )
            == "Select a mailbox"
        )

        assert (
            section.size_value.get()
            == ""
        )

        assert (
            section.details_widget
            .winfo_manager()
            == "grid"
        )

        assert (
            section.header_widget
            .winfo_manager()
            == "grid"
        )

        assert (
            section.header_separator
            .winfo_manager()
            == "grid"
        )

    finally:
        root.destroy()


def test_message_preview_section_has_complete_structure():
    root = tk.Tk()
    root.withdraw()

    try:
        section = MessagePreviewSection(
            root,
            view_model=(
                MessagePreviewViewModel(
                    FakeExplorer()
                )
            ),
        )

        assert hasattr(
            section,
            "header_widget",
        )
        assert hasattr(
            section,
            "header_separator",
        )
        assert hasattr(
            section,
            "body_value",
        )

        assert section.field_labels == (
            "From",
            "To",
            "Subject",
            "Size",
            "Date",
            "UID",
            "Flags",
        )

        assert (
            str(
                section.body_value.cget(
                    "state"
                )
            )
            == "disabled"
        )

    finally:
        root.destroy()


def test_message_preview_section_displays_message():
    root = tk.Tk()
    root.withdraw()

    try:
        view_model = (
            MessagePreviewViewModel(
                MessageExplorer()
            )
        )

        view_model.select_message(
            mailbox="bob@test.onion",
            message_id="message-1",
        )

        section = MessagePreviewSection(
            root,
            view_model=view_model,
        )

        assert (
            section.sender_value.get()
            == "Alice <alice@test.onion>"
        )
        assert (
            section.recipients_value.get()
            == "bob@test.onion"
        )
        assert (
            section.subject_value.get()
            == "GarlicSMTP Preview"
        )
        assert (
            section.size_value.get()
            == view_model.size_text
        )
        assert (
            section.date_value.get()
            == view_model.internal_date_text
        )
        assert (
            section.uid_value.get()
            == "12"
        )
        assert "\\Seen" in (
            section.flags_value.get()
        )

        assert (
            section.body_value.get(
                "1.0",
                "end-1c",
            )
            == "Hello from GarlicSMTP"
        )

        assert (
            section.details_widget
            .winfo_manager()
            == "grid"
        )

        assert (
            section.placeholder_value
            .winfo_manager()
            == ""
        )

    finally:
        root.destroy()


def test_message_preview_section_clears_missing_message():
    root = tk.Tk()
    root.withdraw()

    try:
        view_model = (
            MessagePreviewViewModel(
                MessageExplorer()
            )
        )

        view_model.select_message(
            mailbox="bob@test.onion",
            message_id="message-1",
        )

        section = MessagePreviewSection(
            root,
            view_model=view_model,
        )

        assert (
            section.subject_value.get()
            == "GarlicSMTP Preview"
        )

        view_model.select_message(
            mailbox="bob@test.onion",
            message_id="missing",
        )

        section.refresh_view()

        assert (
            section.placeholder_value.cget(
                "text"
            )
            == "Message unavailable"
        )

        assert (
            section.details_widget
            .winfo_manager()
            == "grid"
        )

        assert (
            section.header_widget
            .winfo_manager()
            == "grid"
        )

        assert (
            section.header_separator
            .winfo_manager()
            == "grid"
        )

        assert (
            section.sender_value.get()
            == ""
        )
        assert (
            section.recipients_value.get()
            == ""
        )
        assert (
            section.subject_value.get()
            == ""
        )
        assert (
            section.size_value.get()
            == ""
        )
        assert (
            section.date_value.get()
            == ""
        )
        assert (
            section.uid_value.get()
            == ""
        )
        assert (
            section.flags_value.get()
            == ""
        )

        assert (
            section.body_value.get(
                "1.0",
                "end-1c",
            )
            == ""
        )

    finally:
        root.destroy()


def test_message_preview_section_displays_safe_html_fallback():
    root = tk.Tk()
    root.withdraw()

    class HtmlExplorer:

        def get_message(
            self,
            mailbox,
            message_id,
        ):
            if (
                mailbox
                == "bob@test.onion"
                and message_id
                == "message-1"
            ):
                entry = make_entry()

                entry.message.headers.add(
                    "Content-Type",
                    "text/html; charset=utf-8",
                )

                entry.message.body = (
                    "<p>Hello from "
                    "<strong>GarlicSMTP</strong></p>"
                )

                return entry

            return None

    try:
        view_model = (
            MessagePreviewViewModel(
                HtmlExplorer()
            )
        )

        view_model.select_message(
            mailbox="bob@test.onion",
            message_id="message-1",
        )

        section = MessagePreviewSection(
            root,
            view_model=view_model,
        )

        assert (
            section.body_value.get(
                "1.0",
                "end-1c",
            )
            == "Hello from GarlicSMTP"
        )

    finally:
        root.destroy()


def test_message_preview_section_separates_header_and_body():
    root = tk.Tk()
    root.withdraw()

    try:
        view_model = (
            MessagePreviewViewModel(
                MessageExplorer()
            )
        )

        view_model.select_message(
            mailbox="bob@test.onion",
            message_id="message-1",
        )

        section = MessagePreviewSection(
            root,
            view_model=view_model,
        )

        assert (
            section.header_widget
            is not section.body_value
        )
        assert (
            section.header_separator
            is not section.body_value
        )

        assert (
            section.header_widget
            .grid_info()["row"]
            == 0
        )
        assert (
            section.header_separator
            .grid_info()["row"]
            == 1
        )
        assert (
            section.body_value
            .grid_info()["row"]
            == 2
        )

        assert (
            str(
                section.body_value.cget(
                    "state"
                )
            )
            == "disabled"
        )

    finally:
        root.destroy()


def test_message_preview_section_uses_bold_header_labels():
    root = tk.Tk()
    root.withdraw()

    try:
        section = MessagePreviewSection(
            root,
            view_model=(
                MessagePreviewViewModel(
                    FakeExplorer()
                )
            ),
        )

        labels = [
            child
            for child in (
                section.header_widget
                .winfo_children()
            )
            if isinstance(
                child,
                ttk.Label,
            )
        ]

        assert len(labels) == 7

        assert all(
            label.cget("style")
            == "Garlic.Header.TLabel"
            for label in labels
        )

    finally:
        root.destroy()


def test_message_preview_body_uses_input_palette():
    root = tk.Tk()
    root.withdraw()

    try:
        section = MessagePreviewSection(
            root,
            view_model=(
                MessagePreviewViewModel(
                    FakeExplorer()
                )
            ),
        )

        assert (
            section.body_value.cget(
                "background"
            )
            == "#ffffff"
        )

        assert (
            section.body_value.cget(
                "foreground"
            )
            == "#000000"
        )

        assert (
            section.body_value.cget(
                "selectbackground"
            )
            == "#ff8c00"
        )

    finally:
        root.destroy()


def test_message_preview_placeholder_is_visible_when_no_message_is_selected():
    root = tk.Tk()
    root.geometry("980x720")

    try:
        section = MessagePreviewSection(
            root,
            view_model=(
                MessagePreviewViewModel(
                    FakeExplorer()
                )
            ),
        )

        section.pack(
            fill="both",
            expand=True,
        )

        root.update_idletasks()

        assert (
            section.placeholder_value
            .winfo_ismapped()
        )

        assert (
            section.placeholder_value
            .winfo_height()
            > 1
        )

    finally:
        root.destroy()


def test_message_preview_body_stays_visible_without_selected_message():
    root = tk.Tk()
    root.geometry("980x720")

    try:
        section = MessagePreviewSection(
            root,
            view_model=(
                MessagePreviewViewModel(
                    FakeExplorer()
                )
            ),
        )

        section.pack(
            fill="both",
            expand=True,
        )

        root.update_idletasks()

        assert (
            section.body_value
            .winfo_ismapped()
        )

    finally:
        root.destroy()