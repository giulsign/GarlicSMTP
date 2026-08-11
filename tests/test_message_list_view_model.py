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
