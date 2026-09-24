# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from datetime import UTC, datetime

from garlicsmtp.application import (
    MessageListViewModel,
    MessageSummary,
)


def make_summary(
    *,
    message_id: str,
    uid: int,
    subject: str,
) -> MessageSummary:
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
        size=128,
        flags=(),
    )


class FakeMessageExplorer:

    def __init__(self):
        self.mailboxes = {
            "alice@test.onion": (
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
            ),
            "empty@test.onion": (),
        }
        self.mark_read_calls = []
        self.mark_unread_calls = []
        self.delete_calls = []

        self.calls = []

    def list_messages(
        self,
        mailbox: str,
    ):
        self.calls.append(
            mailbox
        )

        return self.mailboxes.get(
            mailbox,
            (),
        )

    def mark_read(
        self,
        mailbox: str,
        message_id: str,
    ):
        self.mark_read_calls.append(
            (
                mailbox,
                message_id,
            )
        )

        return True

    def mark_unread(
        self,
        mailbox: str,
        message_id: str,
    ):
        self.mark_unread_calls.append(
            (
                mailbox,
                message_id,
            )
        )

        return True

    def delete_message(
        self,
        mailbox: str,
        message_id: str,
    ):
        self.delete_calls.append(
            (
                mailbox,
                message_id,
            )
        )

        messages = self.mailboxes.get(
            mailbox,
            (),
        )

        self.mailboxes[mailbox] = tuple(
            message
            for message in messages
            if message.id != message_id
        )

        return True



def test_message_list_view_model_selects_mailbox():
    explorer = FakeMessageExplorer()

    view_model = MessageListViewModel(
        explorer
    )

    view_model.select_mailbox(
        "alice@test.onion"
    )

    assert view_model.selected_mailbox == (
        "alice@test.onion"
    )

    assert view_model.message_count == 2

    assert [
        message.subject
        for message in view_model.messages
    ] == [
        "First",
        "Second",
    ]

    assert explorer.calls == [
        "alice@test.onion",
    ]


def test_message_list_view_model_handles_empty_mailbox():
    view_model = MessageListViewModel(
        FakeMessageExplorer()
    )

    view_model.select_mailbox(
        "empty@test.onion"
    )

    assert view_model.empty is True
    assert view_model.message_count == 0
    assert view_model.message_count_text == (
        "No messages"
    )


def test_message_list_view_model_handles_no_mailbox():
    view_model = MessageListViewModel(
        FakeMessageExplorer()
    )

    assert view_model.selected_mailbox is None
    assert view_model.messages == ()
    assert view_model.message_count_text == (
        "No mailbox selected"
    )


def test_message_list_view_model_selects_message():
    view_model = MessageListViewModel(
        FakeMessageExplorer()
    )

    view_model.select_mailbox(
        "alice@test.onion"
    )

    assert view_model.select_message(
        "message-2"
    ) is True

    assert (
        view_model.selected_message_id
        == "message-2"
    )

    assert (
        view_model.selected_message
        is not None
    )

    assert (
        view_model.selected_message.subject
        == "Second"
    )


def test_message_list_view_model_rejects_unknown_message():
    view_model = MessageListViewModel(
        FakeMessageExplorer()
    )

    view_model.select_mailbox(
        "alice@test.onion"
    )

    assert view_model.select_message(
        "missing"
    ) is False

    assert (
        view_model.selected_message_id
        is None
    )


def test_message_list_view_model_clears_selection_on_mailbox_change():
    view_model = MessageListViewModel(
        FakeMessageExplorer()
    )

    view_model.select_mailbox(
        "alice@test.onion"
    )

    view_model.select_message(
        "message-1"
    )

    view_model.select_mailbox(
        "empty@test.onion"
    )

    assert (
        view_model.selected_message_id
        is None
    )

    assert (
        view_model.selected_message
        is None
    )


def test_message_list_view_model_preserves_existing_selection():
    explorer = FakeMessageExplorer()

    view_model = MessageListViewModel(
        explorer
    )

    view_model.select_mailbox(
        "alice@test.onion"
    )

    view_model.select_message(
        "message-1"
    )

    view_model.refresh()

    assert (
        view_model.selected_message_id
        == "message-1"
    )


def test_message_list_view_model_clears_missing_selection():
    explorer = FakeMessageExplorer()

    view_model = MessageListViewModel(
        explorer
    )

    view_model.select_mailbox(
        "alice@test.onion"
    )

    view_model.select_message(
        "message-1"
    )

    explorer.mailboxes[
        "alice@test.onion"
    ] = (
        make_summary(
            message_id="message-2",
            uid=2,
            subject="Second",
        ),
    )

    view_model.refresh()

    assert (
        view_model.selected_message_id
        is None
    )


def test_message_list_view_model_notifies_listeners():
    view_model = MessageListViewModel(
        FakeMessageExplorer()
    )

    notifications = []

    view_model.subscribe(
        lambda: notifications.append(
            "changed"
        )
    )

    view_model.select_mailbox(
        "alice@test.onion"
    )

    view_model.select_message(
        "message-1"
    )

    assert notifications == [
        "changed",
        "changed",
    ]


def test_message_list_view_model_marks_selected_message_as_read():
    explorer = FakeMessageExplorer()

    view_model = MessageListViewModel(
        explorer
    )

    view_model.select_mailbox(
        "alice@test.onion"
    )

    view_model.select_message(
        "message-1"
    )

    result = (
        view_model.mark_selected_read()
    )

    assert result is True

    assert explorer.mark_read_calls == [
        (
            "alice@test.onion",
            "message-1",
        ),
    ]


def test_message_list_view_model_marks_selected_message_as_unread():
    explorer = FakeMessageExplorer()

    view_model = MessageListViewModel(
        explorer
    )

    view_model.select_mailbox(
        "alice@test.onion"
    )

    view_model.select_message(
        "message-2"
    )

    result = (
        view_model.mark_selected_unread()
    )

    assert result is True

    assert explorer.mark_unread_calls == [
        (
            "alice@test.onion",
            "message-2",
        ),
    ]


def test_message_list_view_model_deletes_selected_message():
    explorer = FakeMessageExplorer()

    view_model = MessageListViewModel(
        explorer
    )

    view_model.select_mailbox(
        "alice@test.onion"
    )

    view_model.select_message(
        "message-1"
    )

    result = (
        view_model.delete_selected()
    )

    assert result is True

    assert explorer.delete_calls == [
        (
            "alice@test.onion",
            "message-1",
        ),
    ]

    assert (
        view_model.selected_message_id
        is None
    )

    assert [
        message.id
        for message in view_model.messages
    ] == [
        "message-2",
    ]
