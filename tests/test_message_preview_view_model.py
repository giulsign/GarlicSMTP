from datetime import UTC, datetime

from garlicsmtp.application import (
    MessagePreviewViewModel,
)
from garlicsmtp.models import (
    Envelope,
    MailHeaders,
    MailMessage,
    Metadata,
)
from garlicsmtp.storage.entry import (
    MessageEntry,
)


def make_entry(
    *,
    message_id="message-1",
    uid=7,
    sender="alice@test.onion",
    header_sender=None,
    recipients=(
        "bob@test.onion",
    ),
    subject="GarlicSMTP",
    body="Hello from GarlicSMTP",
    flags=(),
    size=128,
):
    headers = MailHeaders()

    if header_sender is not None:
        headers.add(
            "From",
            header_sender,
        )

    if subject is not None:
        headers.add(
            "Subject",
            subject,
        )

    return MessageEntry(
        id=message_id,
        mailbox="bob@test.onion",
        uid=uid,
        message=MailMessage(
            envelope=Envelope(
                sender=sender,
                recipients=list(
                    recipients
                ),
            ),
            headers=headers,
            metadata=Metadata(
                size=size,
            ),
            body=body,
        ),
        internal_date=datetime(
            2026,
            8,
            7,
            9,
            30,
            tzinfo=UTC,
        ),
        flags=set(
            flags
        ),
    )


class FakeExplorer:

    def __init__(
        self,
    ):
        self.entries = {
            (
                "bob@test.onion",
                "message-1",
            ): make_entry(),
        }

        self.calls = []

    def get_message(
        self,
        mailbox,
        message_id,
    ):
        self.calls.append(
            (
                mailbox,
                message_id,
            )
        )

        return self.entries.get(
            (
                mailbox,
                message_id,
            )
        )


def test_message_preview_starts_empty():
    view_model = MessagePreviewViewModel(
        FakeExplorer()
    )

    assert view_model.has_message is False
    assert view_model.mailbox is None
    assert view_model.message_id is None
    assert view_model.sender == ""
    assert view_model.subject == ""
    assert view_model.body == ""
    assert view_model.placeholder_text == (
        "Select a mailbox"
    )


def test_message_preview_loads_message():
    explorer = FakeExplorer()

    view_model = MessagePreviewViewModel(
        explorer
    )

    view_model.select_message(
        mailbox="bob@test.onion",
        message_id="message-1",
    )

    assert view_model.has_message is True

    assert view_model.sender == (
        "alice@test.onion"
    )

    assert view_model.recipients == (
        "bob@test.onion",
    )

    assert view_model.recipients_text == (
        "bob@test.onion"
    )

    assert view_model.subject == (
        "GarlicSMTP"
    )

    assert view_model.uid == 7
    assert view_model.uid_text == "7"

    assert view_model.body == (
        "Hello from GarlicSMTP"
    )

    assert view_model.placeholder_text == ""

    assert explorer.calls == [
        (
            "bob@test.onion",
            "message-1",
        ),
    ]


def test_message_preview_prefers_from_header():
    explorer = FakeExplorer()

    explorer.entries[
        (
            "bob@test.onion",
            "message-1",
        )
    ] = make_entry(
        header_sender=(
            "Alice <alice@test.onion>"
        )
    )

    view_model = MessagePreviewViewModel(
        explorer
    )

    view_model.select_message(
        mailbox="bob@test.onion",
        message_id="message-1",
    )

    assert view_model.sender == (
        "Alice <alice@test.onion>"
    )


def test_message_preview_formats_missing_subject():
    explorer = FakeExplorer()

    explorer.entries[
        (
            "bob@test.onion",
            "message-1",
        )
    ] = make_entry(
        subject=None
    )

    view_model = MessagePreviewViewModel(
        explorer
    )

    view_model.select_message(
        mailbox="bob@test.onion",
        message_id="message-1",
    )

    assert view_model.subject == (
        "(No subject)"
    )


def test_message_preview_formats_flags():
    explorer = FakeExplorer()

    explorer.entries[
        (
            "bob@test.onion",
            "message-1",
        )
    ] = make_entry(
        flags=(
            "\\Seen",
            "\\Flagged",
        )
    )

    view_model = MessagePreviewViewModel(
        explorer
    )

    view_model.select_message(
        mailbox="bob@test.onion",
        message_id="message-1",
    )

    assert view_model.flags == (
        "\\Flagged",
        "\\Seen",
    )

    assert "\\Seen" in (
        view_model.flags_text
    )

    assert "\\Flagged" in (
        view_model.flags_text
    )


def test_message_preview_handles_missing_message():
    view_model = MessagePreviewViewModel(
        FakeExplorer()
    )

    view_model.select_message(
        mailbox="bob@test.onion",
        message_id="missing",
    )

    assert view_model.has_message is False

    assert view_model.placeholder_text == (
        "Message unavailable"
    )


def test_message_preview_waits_for_message_selection():
    view_model = MessagePreviewViewModel(
        FakeExplorer()
    )

    view_model.select_message(
        mailbox="bob@test.onion",
        message_id=None,
    )

    assert view_model.has_message is False

    assert view_model.placeholder_text == (
        "Select a message"
    )


def test_message_preview_notifies_listener():
    view_model = MessagePreviewViewModel(
        FakeExplorer()
    )

    notifications = []

    view_model.subscribe(
        lambda: notifications.append(
            "changed"
        )
    )

    view_model.select_message(
        mailbox="bob@test.onion",
        message_id="message-1",
    )

    assert notifications == [
        "changed",
    ]


def test_message_preview_clears_selection():
    view_model = MessagePreviewViewModel(
        FakeExplorer()
    )

    view_model.select_message(
        mailbox="bob@test.onion",
        message_id="message-1",
    )

    view_model.clear()

    assert view_model.has_message is False
    assert view_model.mailbox is None
    assert view_model.message_id is None

    assert view_model.placeholder_text == (
        "Select a mailbox"
    )


def test_message_preview_refreshes_message():
    explorer = FakeExplorer()

    view_model = MessagePreviewViewModel(
        explorer
    )

    view_model.select_message(
        mailbox="bob@test.onion",
        message_id="message-1",
    )

    explorer.entries[
        (
            "bob@test.onion",
            "message-1",
        )
    ] = make_entry(
        subject="Updated subject"
    )

    view_model.refresh()

    assert view_model.subject == (
        "Updated subject"
    )


def test_message_preview_view_model_exposes_size_text():
    explorer = FakeExplorer()

    view_model = MessagePreviewViewModel(
        explorer
    )

    view_model.select_message(
        mailbox="bob@test.onion",
        message_id="message-1",
    )

    assert view_model.size_text == "128 B"

def test_message_preview_view_model_formats_size_in_kilobytes():
    explorer = FakeExplorer()

    explorer.entries[
        (
            "bob@test.onion",
            "message-1",
        )
    ] = make_entry(
        size=2048,
    )

    view_model = MessagePreviewViewModel(
        explorer
    )

    view_model.select_message(
        mailbox="bob@test.onion",
        message_id="message-1",
    )

    assert view_model.size_text == "2.0 KB"


def test_message_preview_view_model_formats_size_in_megabytes():
    explorer = FakeExplorer()

    explorer.entries[
        (
            "bob@test.onion",
            "message-1",
        )
    ] = make_entry(
        size=2 * 1024 * 1024,
    )

    view_model = MessagePreviewViewModel(
        explorer
    )

    view_model.select_message(
        mailbox="bob@test.onion",
        message_id="message-1",
    )

    assert view_model.size_text == "2.0 MB"

