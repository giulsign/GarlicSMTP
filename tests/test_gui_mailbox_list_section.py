# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.application import (
    ApplicationViewModel,
    MailboxSummary,
)
from garlicsmtp.gui.sections import (
    MailboxListSection,
)
from tests.support import (
    make_application_status,
)
from tests.test_gui_main_window import (
    FakeController,
    get_application,
)


def build_section():
    get_application()

    controller = FakeController()

    controller.current_status = (
        make_application_status(
            mailboxes=(
                "alice@test.onion",
                "bob@test.onion",
            ),
            mailbox_summaries=(
                MailboxSummary(
                    address=(
                        "alice@test.onion"
                    ),
                    message_count=3,
                ),
                MailboxSummary(
                    address=(
                        "bob@test.onion"
                    ),
                    message_count=1,
                ),
            ),
        )
    )

    section = MailboxListSection(
        view_model=ApplicationViewModel(
            controller
        )
    )

    section.refresh_view()

    return section


def test_mailbox_list_section_displays_mailboxes():
    section = build_section()

    assert section.mailbox_list.count() == 2

    assert "alice@test.onion" in (
        section.mailbox_list
        .item(0)
        .text()
    )

    assert "3 messages" in (
        section.mailbox_list
        .item(0)
        .text()
    )

    assert section.summary_value.text() == (
        "2 mailboxes, 4 messages"
    )

    section.close()


def test_mailbox_list_section_selects_mailbox():
    section = build_section()

    selected = []

    section.mailbox_selected.connect(
        selected.append
    )

    assert section.select_mailbox(
        "bob@test.onion"
    ) is True

    assert section.selected_mailbox == (
        "bob@test.onion"
    )

    assert selected == [
        "bob@test.onion",
    ]

    section.close()


def test_mailbox_list_section_preserves_selection():
    section = build_section()

    section.select_mailbox(
        "bob@test.onion"
    )

    section.refresh_view()

    assert section.selected_mailbox == (
        "bob@test.onion"
    )

    section.close()


def test_mailbox_list_section_rejects_unknown_selection():
    section = build_section()

    assert section.select_mailbox(
        "missing@test.onion"
    ) is False

    section.close()
