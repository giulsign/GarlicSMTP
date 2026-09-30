# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import tkinter as tk
from pathlib import Path

from garlicsmtp.application.compose_view_model import (
    ComposeViewModel,
)
from garlicsmtp.gui.tk_compose_section import (
    ComposeSection,
)
import garlicsmtp.gui.tk_compose_section as compose_module


class FakeComposer:

    def send(
        self,
        *,
        sender,
        recipient,
        subject,
        body,
        attachments=None,
    ):
        del sender
        del recipient
        del subject
        del body
        del attachments

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
                attachments=None,
            ):
                self.calls.append(
                    {
                        "sender": sender,
                        "recipient": recipient,
                        "subject": subject,
                        "body": body,
                        "attachments": attachments,
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
                "attachments": [],
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
                attachments=None,
            ):
                del sender
                del recipient
                del subject
                del body
                del attachments

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
                attachments=None,
            ):
                del sender
                del recipient
                del subject
                del body
                del attachments

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


def test_compose_section_attaches_selected_file(
    tmp_path,
):
    root = tk.Tk()
    root.withdraw()

    try:
        attachment_path = (
            tmp_path / "note.txt"
        )
        attachment_path.write_bytes(
            b"Hello attachment"
        )

        view_model = ComposeViewModel(
            FakeComposer()
        )

        section = ComposeSection(
            root,
            view_model=view_model,
        )

        section._attach_file(
            attachment_path
        )

        assert len(
            view_model.attachments
        ) == 1

        attachment = (
            view_model.attachments[0]
        )

        assert attachment.filename == (
            "note.txt"
        )
        assert attachment.declared_mime == (
            "text/plain"
        )
        assert attachment.content == (
            b"Hello attachment"
        )

    finally:
        root.destroy()


def test_compose_section_attach_button_selects_file(
    tmp_path,
    monkeypatch,
):
    root = tk.Tk()
    root.withdraw()

    try:
        attachment_path = (
            tmp_path / "note.txt"
        )
        attachment_path.write_bytes(
            b"Hello attachment"
        )

        monkeypatch.setattr(
            compose_module.filedialog,
            "askopenfilename",
            lambda **kwargs: str(
                attachment_path
            ),
        )

        view_model = ComposeViewModel(
            FakeComposer()
        )

        section = ComposeSection(
            root,
            view_model=view_model,
        )

        section.attach_button.invoke()

        assert len(
            view_model.attachments
        ) == 1

        attachment = (
            view_model.attachments[0]
        )

        assert attachment.filename == (
            "note.txt"
        )
        assert attachment.declared_mime == (
            "text/plain"
        )
        assert attachment.content == (
            b"Hello attachment"
        )

    finally:
        root.destroy()


def test_compose_section_attach_cancel_does_nothing(
    monkeypatch,
):
    root = tk.Tk()
    root.withdraw()

    try:
        monkeypatch.setattr(
            compose_module.filedialog,
            "askopenfilename",
            lambda **kwargs: "",
        )

        view_model = ComposeViewModel(
            FakeComposer()
        )

        section = ComposeSection(
            root,
            view_model=view_model,
        )

        section.attach_button.invoke()

        assert view_model.attachments == []

    finally:
        root.destroy()


def test_compose_section_shows_attached_filename(
    tmp_path,
):
    root = tk.Tk()
    root.withdraw()

    try:
        attachment_path = (
            tmp_path / "note.txt"
        )
        attachment_path.write_bytes(
            b"Hello attachment"
        )

        section = ComposeSection(
            root,
            view_model=ComposeViewModel(
                FakeComposer()
            ),
        )

        section._attach_file(
            attachment_path
        )

        assert (
            section.attachment_label.cget(
                "text"
            )
            == "note.txt"
        )

    finally:
        root.destroy()


def test_compose_section_clear_button_clears_attachment(
    tmp_path,
):
    root = tk.Tk()
    root.withdraw()

    try:
        attachment_path = (
            tmp_path / "note.txt"
        )
        attachment_path.write_bytes(
            b"Hello attachment"
        )

        view_model = ComposeViewModel(
            FakeComposer()
        )
        section = ComposeSection(
            root,
            view_model=view_model,
        )

        section._attach_file(
            attachment_path
        )

        section.clear_button.invoke()

        assert view_model.attachments == []
        assert (
            section.attachment_label.cget(
                "text"
            )
            == ""
        )

    finally:
        root.destroy()


def test_compose_section_failed_send_preserves_attachment(
    tmp_path,
):
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
                attachments=None,
            ):
                del sender
                del recipient
                del subject
                del body
                del attachments

                return False

        attachment_path = (
            tmp_path / "note.txt"
        )
        attachment_path.write_bytes(
            b"Hello attachment"
        )

        view_model = ComposeViewModel(
            FailingComposer()
        )
        section = ComposeSection(
            root,
            view_model=view_model,
        )

        section._attach_file(
            attachment_path
        )

        section.send_button.invoke()

        assert len(
            view_model.attachments
        ) == 1
        assert (
            view_model.attachments[0].filename
            == "note.txt"
        )
        assert (
            section.attachment_label.cget(
                "text"
            )
            == "note.txt"
        )

    finally:
        root.destroy()


def test_compose_section_successful_send_clears_attachment(
    tmp_path,
):
    root = tk.Tk()
    root.withdraw()

    try:
        attachment_path = (
            tmp_path / "note.txt"
        )
        attachment_path.write_bytes(
            b"Hello attachment"
        )

        view_model = ComposeViewModel(
            FakeComposer()
        )
        section = ComposeSection(
            root,
            view_model=view_model,
        )

        section._attach_file(
            attachment_path
        )

        section.send_button.invoke()

        assert view_model.attachments == []
        assert (
            section.attachment_label.cget(
                "text"
            )
            == ""
        )

    finally:
        root.destroy()