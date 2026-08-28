# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from datetime import UTC, datetime

from garlicsmtp.application import (
    MessageListViewModel,
    MessageSummary,
)
from garlicsmtp.gui.sections import (
    MessageListSection,
)
from tests.test_gui_main_window import (
    get_application,
)
from garlicsmtp.application import (
    MessageFormatter,
)
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import (
    QMessageBox,
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
    get_application()

    view_model = MessageListViewModel(
        FakeExplorer()
    )

    view_model.select_mailbox(
        "bob@test.onion"
    )

    section = MessageListSection(
        view_model=view_model
    )

    section.refresh_view()

    return section, view_model


def test_message_list_section_displays_messages():
    section, _ = build_section()

    assert section.table.rowCount() == 2

    assert (
        section.table.item(
            0,
            section.COLUMN_SUBJECT,
        ).text()
        == "Unread"
    )

    assert (
        section.table.item(
            1,
            section.COLUMN_SIZE,
        ).text()
        == "2.0 KB"
    )

    section.close()


def test_message_list_section_displays_flags():
    section, _ = build_section()

    assert "●" in (
        section.table.item(
            0,
            section.COLUMN_STATUS,
        ).text()
    )

    assert "⚑" in (
        section.table.item(
            1,
            section.COLUMN_STATUS,
        ).text()
    )

    section.close()


def test_message_list_section_selects_message():
    section, view_model = build_section()

    selected = []

    section.message_selected.connect(
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

    section.close()


def test_message_list_section_rejects_unknown_message():
    section, view_model = build_section()

    assert section.select_message(
        "missing"
    ) is False

    assert (
        view_model.selected_message_id
        is None
    )

    section.close()


def test_message_list_section_handles_empty_mailbox():
    get_application()

    class EmptyExplorer:

        def list_messages(
            self,
            mailbox,
        ):
            del mailbox
            return ()

    view_model = MessageListViewModel(
        EmptyExplorer()
    )

    view_model.select_mailbox(
        "empty@test.onion"
    )

    section = MessageListSection(
        view_model=view_model
    )

    section.refresh_view()

    assert section.table.rowCount() == 0
    assert section.selected_message_id is None

    section.close()


def test_message_list_section_preserves_selection():
    section, view_model = build_section()

    section.select_message(
        "message-1"
    )

    section.refresh_view()

    assert (
        section.selected_message_id
        == "message-1"
    )

    assert (
        view_model.selected_message_id
        == "message-1"
    )

    section.close()


def test_message_list_section_uses_formatter():
    get_application()

    class CustomFormatter(
        MessageFormatter
    ):

        def format_subject(
            self,
            message,
        ):
            del message
            return "Formatted subject"

    view_model = MessageListViewModel(
        FakeExplorer()
    )

    view_model.select_mailbox(
        "bob@test.onion"
    )

    section = MessageListSection(
        view_model=view_model,
        formatter=CustomFormatter(),
    )

    section.refresh_view()

    assert (
        section.table.item(
            0,
            section.COLUMN_SUBJECT,
        ).text()
        == "Formatted subject"
    )

    section.close()


def test_message_list_section_navigates_with_keyboard():
    section, view_model = build_section()

    selected = []

    section.message_selected.connect(
        selected.append
    )

    assert section.select_message(
        "message-1"
    ) is True

    section.table.setFocus()

    QTest.keyClick(
        section.table,
        Qt.Key.Key_Down,
    )

    assert (
        section.selected_message_id
        == "message-2"
    )

    assert (
        view_model.selected_message_id
        == "message-2"
    )

    assert selected[-1] == "message-2"

    section.close()


def test_message_list_section_has_refresh_button():
    section, _ = build_section()

    assert hasattr(
        section,
        "refresh_button",
    )

    assert (
        section.refresh_button.text()
        == "Refresh"
    )

    section.close()


def test_message_list_section_refresh_button_updates_messages():
    get_application()

    class MutableExplorer:

        def __init__(
            self,
        ):
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
        view_model=view_model
    )

    section.refresh_view()

    assert section.table.rowCount() == 1

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

    section.refresh_button.click()

    assert section.table.rowCount() == 2

    assert (
        section.table.item(
            1,
            section.COLUMN_SUBJECT,
        ).text()
        == "Second"
    )

    section.close()


def test_message_list_section_has_mark_read_button():
    section, _ = build_section()

    assert hasattr(
        section,
        "mark_read_button",
    )

    assert (
        section.mark_read_button.text()
        == "Mark read"
    )

    section.close()


def test_message_list_section_mark_read_button_marks_selected_message():
    section, view_model = build_section()

    section.select_message(
        "message-1"
    )

    calls = []

    view_model.mark_selected_read = (
        lambda: calls.append(
            "mark_read"
        ) or True
    )

    section.mark_read_button.click()

    assert calls == [
        "mark_read",
    ]

    section.close()


def test_message_list_section_has_mark_unread_button():
    section, _ = build_section()

    assert hasattr(
        section,
        "mark_unread_button",
    )

    assert (
        section.mark_unread_button.text()
        == "Mark unread"
    )

    section.close()


def test_message_list_section_mark_unread_button_marks_selected_message():
    section, view_model = build_section()

    section.select_message(
        "message-2"
    )

    calls = []

    view_model.mark_selected_unread = (
        lambda: calls.append(
            "mark_unread"
        ) or True
    )

    section.mark_unread_button.click()

    assert calls == [
        "mark_unread",
    ]

    section.close()


def test_message_list_section_has_delete_button():
    section, _ = build_section()

    assert hasattr(
        section,
        "delete_button",
    )

    assert (
        section.delete_button.text()
        == "Delete"
    )

    section.close()


def test_message_list_section_delete_requires_confirmation(
    monkeypatch,
):
    section, view_model = build_section()

    section.select_message(
        "message-1"
    )

    calls = []

    view_model.delete_selected = (
        lambda: calls.append(
            "delete"
        ) or True
    )

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: (
            QMessageBox.StandardButton.No
        ),
    )

    section.delete_button.click()

    assert calls == []

    section.close()


def test_message_list_section_delete_confirms_selected_message(
    monkeypatch,
):
    section, view_model = build_section()

    section.select_message(
        "message-1"
    )

    calls = []

    view_model.delete_selected = (
        lambda: calls.append(
            "delete"
        ) or True
    )

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: (
            QMessageBox.StandardButton.Yes
        ),
    )

    section.delete_button.click()

    assert calls == [
        "delete",
    ]

    section.close()


def test_message_list_section_groups_actions_in_toolbar():
    section, _ = build_section()

    assert hasattr(
        section,
        "toolbar_widget",
    )

    toolbar_layout = (
        section.toolbar_widget.layout()
    )

    assert (
        toolbar_layout.itemAt(0).widget()
        is section.refresh_button
    )

    assert (
        toolbar_layout.itemAt(1).widget()
        is section.mark_read_button
    )

    assert (
        toolbar_layout.itemAt(2).widget()
        is section.mark_unread_button
    )

    assert (
        toolbar_layout.itemAt(3).widget()
        is section.delete_button
    )

    section.close()