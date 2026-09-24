# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import tkinter as tk

from garlicsmtp.application.compose_view_model import (
    ComposeViewModel,
)
from garlicsmtp.gui.tk_compose_section import (
    ComposeSection,
)


class FakeComposer:

    def send(
        self,
        *,
        sender,
        recipient,
        subject,
        body,
    ):
        del sender
        del recipient
        del subject
        del body

        return True


def test_compose_section_has_required_fields():
    root = tk.Tk()
    root.withdraw()

    try:
        section = ComposeSection(
            root,
            view_model=ComposeViewModel(
                FakeComposer()
            ),
        )

        assert hasattr(
            section,
            "sender_input",
        )
        assert hasattr(
            section,
            "recipient_input",
        )
        assert hasattr(
            section,
            "subject_input",
        )
        assert hasattr(
            section,
            "body_input",
        )
        assert hasattr(
            section,
            "send_button",
        )
        assert hasattr(
            section,
            "clear_button",
        )

        assert (
            section.send_button.cget("text")
            == "Send"
        )
        assert (
            section.clear_button.cget("text")
            == "Clear"
        )

    finally:
        root.destroy()


def test_compose_section_refreshes_sender_from_view_model():
    root = tk.Tk()
    root.withdraw()

    try:
        view_model = ComposeViewModel(
            FakeComposer()
        )

        section = ComposeSection(
            root,
            view_model=view_model,
        )

        view_model.sender = (
            "garlicsmtp@"
            + ("a" * 56)
            + ".onion"
        )

        section.refresh_view()

        assert (
            section.sender_input.get()
            == view_model.sender
        )

    finally:
        root.destroy()


def test_compose_section_send_uses_view_model():
    root = tk.Tk()
    root.withdraw()

    try:
        class RecordingComposer:

            def __init__(self):
                self.calls = []

            def send(
                self,
                *,
                sender,
                recipient,
                subject,
                body,
            ):
                self.calls.append(
                    {
                        "sender": sender,
                        "recipient": recipient,
                        "subject": subject,
                        "body": body,
                    }
                )

                return True

        composer = RecordingComposer()

        section = ComposeSection(
            root,
            view_model=ComposeViewModel(
                composer
            ),
        )

        section.sender_input.insert(
            0,
            "alice@sender.onion",
        )
        section.recipient_input.insert(
            0,
            "bob@receiver.onion",
        )
        section.subject_input.insert(
            0,
            "Hello",
        )
        section.body_input.insert(
            "1.0",
            "Hello from GarlicSMTP",
        )

        section.send_button.invoke()

        assert composer.calls == [
            {
                "sender": (
                    "alice@sender.onion"
                ),
                "recipient": (
                    "bob@receiver.onion"
                ),
                "subject": "Hello",
                "body": (
                    "Hello from GarlicSMTP"
                ),
            }
        ]

    finally:
        root.destroy()


def fill_compose_fields(section):
    section.sender_input.insert(
        0,
        "alice@sender.onion",
    )
    section.recipient_input.insert(
        0,
        "bob@receiver.onion",
    )
    section.subject_input.insert(
        0,
        "Hello",
    )
    section.body_input.insert(
        "1.0",
        "Body",
    )


def assert_compose_fields_empty(section):
    assert section.sender_input.get() == ""
    assert section.recipient_input.get() == ""
    assert section.subject_input.get() == ""
    assert (
        section.body_input.get(
            "1.0",
            "end-1c",
        )
        == ""
    )


def test_compose_section_clear_button_clears_fields():
    root = tk.Tk()
    root.withdraw()

    try:
        section = ComposeSection(
            root,
            view_model=ComposeViewModel(
                FakeComposer()
            ),
        )

        fill_compose_fields(section)

        section.clear_button.invoke()

        assert_compose_fields_empty(
            section
        )

    finally:
        root.destroy()


def test_compose_section_successful_send_clears_fields():
    root = tk.Tk()
    root.withdraw()

    try:
        section = ComposeSection(
            root,
            view_model=ComposeViewModel(
                FakeComposer()
            ),
        )

        fill_compose_fields(section)

        section.send_button.invoke()

        assert_compose_fields_empty(
            section
        )

    finally:
        root.destroy()


def test_compose_section_failed_send_preserves_fields():
    root = tk.Tk()
    root.withdraw()

    try:
        class FailingComposer:

            def send(
                self,
                *,
                sender,
                recipient,
                subject,
                body,
            ):
                del sender
                del recipient
                del subject
                del body

                return False

        section = ComposeSection(
            root,
            view_model=ComposeViewModel(
                FailingComposer()
            ),
        )

        fill_compose_fields(section)

        section.send_button.invoke()

        assert (
            section.sender_input.get()
            == "alice@sender.onion"
        )
        assert (
            section.recipient_input.get()
            == "bob@receiver.onion"
        )
        assert (
            section.subject_input.get()
            == "Hello"
        )
        assert (
            section.body_input.get(
                "1.0",
                "end-1c",
            )
            == "Body"
        )

    finally:
        root.destroy()


def test_compose_section_send_exception_is_handled():
    root = tk.Tk()
    root.withdraw()

    try:
        class RaisingComposer:

            def send(
                self,
                *,
                sender,
                recipient,
                subject,
                body,
            ):
                del sender
                del recipient
                del subject
                del body

                raise RuntimeError(
                    "delivery failed"
                )

        section = ComposeSection(
            root,
            view_model=ComposeViewModel(
                RaisingComposer()
            ),
        )

        fill_compose_fields(section)

        section._send_message()

        assert (
            section.recipient_input.get()
            == "bob@receiver.onion"
        )

    finally:
        root.destroy()
