from datetime import UTC, datetime

from garlicsmtp.application import (
    MessagePreviewViewModel,
)
from garlicsmtp.gui.sections import (
    MessagePreviewSection,
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
from tests.test_gui_main_window import (
    get_application,
)
from PySide6.QtWidgets import (
    QFormLayout,
)


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
            metadata=Metadata(
                size=128,
            ),
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


class FakeExplorer:

    def get_message(
        self,
        mailbox,
        message_id,
    ):
        if (
            mailbox == "bob@test.onion"
            and message_id == "message-1"
        ):
            return make_entry()

        return None


def test_message_preview_section_starts_empty():
    get_application()

    view_model = (
        MessagePreviewViewModel(
            FakeExplorer()
        )
    )

    section = MessagePreviewSection(
        view_model=view_model
    )

    assert (
        section.placeholder_value.text()
        == "Select a mailbox"
    )

    assert (
        section.size_value.text()
        == ""
    )

    assert (
        section.details_widget
        .isHidden()
        is True
    )

    section.close()


def test_message_preview_section_displays_message():
    get_application()

    view_model = (
        MessagePreviewViewModel(
            FakeExplorer()
        )
    )

    view_model.select_message(
        mailbox="bob@test.onion",
        message_id="message-1",
    )

    section = MessagePreviewSection(
        view_model=view_model
    )

    section.refresh_view()

    assert (
        section.sender_value.text()
        == "Alice <alice@test.onion>"
    )

    assert (
        section.recipients_value.text()
        == "bob@test.onion"
    )

    assert (
        section.subject_value.text()
        == "GarlicSMTP Preview"
    )

    assert (
        section.size_value.text()
        == "128 B"
    )

    assert section.uid_value.text() == "12"

    assert "\\Seen" in (
        section.flags_value.text()
    )

    assert (
        section.body_value
        .toPlainText()
        == "Hello from GarlicSMTP"
    )

    assert (
        section.details_widget
        .isHidden()
        is False
    )

    section.close()


def test_message_preview_section_handles_missing_message():
    get_application()

    view_model = (
        MessagePreviewViewModel(
            FakeExplorer()
        )
    )

    view_model.select_message(
        mailbox="bob@test.onion",
        message_id="missing",
    )

    section = MessagePreviewSection(
        view_model=view_model
    )

    section.refresh_view()

    assert (
        section.placeholder_value.text()
        == "Message unavailable"
    )

    assert (
        section.size_value.text()
        == ""
    )

    assert (
        section.details_widget
        .isHidden()
        is True
    )

    section.close()


def test_message_preview_section_has_complete_header():
    get_application()

    view_model = (
        MessagePreviewViewModel(
            FakeExplorer()
        )
    )

    view_model.select_message(
        mailbox="bob@test.onion",
        message_id="message-1",
    )

    section = MessagePreviewSection(
        view_model=view_model
    )

    header_widget = (
        section.details_widget
        .layout()
        .itemAt(0)
        .widget()
    )

    header_layout = header_widget.layout()

    assert header_layout.rowCount() == 7

    expected_labels = [
        "From",
        "To",
        "Subject",
        "Size",
        "Date",
        "UID",
        "Flags",
    ]

    actual_labels = [
        header_layout.itemAt(
            row,
            QFormLayout.LabelRole,
        ).widget().text()
        for row in range(
            header_layout.rowCount()
        )
    ]

    assert actual_labels == expected_labels

    assert (
        section.body_value.isReadOnly()
        is True
    )

    section.close()