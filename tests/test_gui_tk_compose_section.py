# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import tkinter as tk
from pathlib import Path
import time

from garlicsmtp.application.compose_view_model import (
    ComposeViewModel,
)
from garlicsmtp.gui.tk_compose_section import (
    ComposeSection,
)
import garlicsmtp.gui.tk_compose_section as compose_module


def wait_for_send_completion(root, section, timeout=3):
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        root.update()

        if not section._send_in_progress:
            return

        time.sleep(0.01)

    raise AssertionError(
        "Asynchronous send did not complete"
    )


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
        wait_for_send_completion(root, section)

        assert_compose_fields_empty(
            section
        )

    finally:
        root.destroy()


def test_compose_section_failed_send_preserves_fields(monkeypatch):
    root = tk.Tk()
    root.withdraw()

    errors = []

    monkeypatch.setattr(
        compose_module.messagebox,
        "showerror",
        lambda title, message, **kwargs: errors.append(
            (title, message)
        ),
    )

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
        wait_for_send_completion(root, section)

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
        assert len(errors) == 1
        assert errors[0][0] == "GarlicSMTP error"
        assert "not sent" in errors[0][1].lower()

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


def test_compose_section_send_exception_shows_error_and_preserves_fields(
    monkeypatch,
):
    root = tk.Tk()
    root.withdraw()

    errors = []

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
            raise RuntimeError("delivery failed")

    try:
        section = ComposeSection(
            root,
            view_model=ComposeViewModel(
                RaisingComposer()
            ),
        )

        fill_compose_fields(section)

        monkeypatch.setattr(
            compose_module.messagebox,
            "showerror",
            lambda title, message, **kwargs: errors.append(
                (title, message)
            ),
        )

        section.send_button.invoke()
        wait_for_send_completion(root, section)

        assert errors == [
            (
                "GarlicSMTP error",
                "Failed to send message: delivery failed",
            )
        ]

        assert section.sender_input.get() == (
            "alice@sender.onion"
        )
        assert section.recipient_input.get() == (
            "bob@receiver.onion"
        )
        assert section.subject_input.get() == "Hello"
        assert section.body_input.get(
            "1.0",
            "end-1c",
        ) == "Body"

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
        wait_for_send_completion(root, section)

        assert view_model.attachments == []
        assert (
            section.attachment_label.cget(
                "text"
            )
            == ""
        )

    finally:
        root.destroy()


def test_compose_section_send_does_not_block_gui():
    import threading

    root = tk.Tk()
    root.withdraw()

    send_started = threading.Event()
    allow_send_to_finish = threading.Event()

    class SlowComposer:

        def send(
            self,
            *,
            sender,
            recipient,
            subject,
            body,
            attachments=None,
        ):
            send_started.set()

            if not allow_send_to_finish.wait(timeout=3):
                raise TimeoutError("Simulated slow send timed out")

            return True

    try:
        section = ComposeSection(
            root,
            view_model=ComposeViewModel(
                SlowComposer()
            ),
        )

        fill_compose_fields(section)

        start = __import__("time").monotonic()
        section.send_button.invoke()
        elapsed = __import__("time").monotonic() - start

        assert elapsed < 0.5
        assert send_started.wait(timeout=1)
        assert str(section.send_button.cget("state")) == "disabled"

    finally:
        allow_send_to_finish.set()
        root.destroy()


def test_compose_section_async_send_clears_only_after_completion():
    import threading
    import time

    root = tk.Tk()
    root.withdraw()

    send_started = threading.Event()
    allow_completion = threading.Event()

    class ControlledComposer:

        def send(
            self,
            *,
            sender,
            recipient,
            subject,
            body,
            attachments=None,
        ):
            send_started.set()

            if not allow_completion.wait(timeout=5):
                raise TimeoutError("Test send timed out")

            return True

    try:
        section = ComposeSection(
            root,
            view_model=ComposeViewModel(
                ControlledComposer()
            ),
        )

        fill_compose_fields(section)
        section.send_button.invoke()

        assert send_started.wait(timeout=1)

        # L'invio è ancora in corso: il messaggio deve restare visibile.
        assert section.subject_input.get() == "Hello"
        assert str(section.send_button.cget("state")) == "disabled"

        allow_completion.set()

        # Il polling Tkinter deve elaborare il risultato.
        deadline = time.monotonic() + 3

        while time.monotonic() < deadline:
            root.update()

            if str(section.send_button.cget("state")) == "normal":
                break

            time.sleep(0.01)

        assert str(section.send_button.cget("state")) == "normal"
        assert str(section.clear_button.cget("state")) == "normal"
        assert str(section.attach_button.cget("state")) == "normal"

        assert section.sender_input.get() == ""
        assert section.recipient_input.get() == ""
        assert section.subject_input.get() == ""
        assert section.body_input.get("1.0", "end-1c") == ""

    finally:
        allow_completion.set()
        root.destroy()


def test_compose_section_destroy_cancels_pending_send_poll():
    import threading

    root = tk.Tk()
    root.withdraw()

    send_started = threading.Event()
    allow_completion = threading.Event()

    class ControlledComposer:

        def send(
            self,
            *,
            sender,
            recipient,
            subject,
            body,
            attachments=None,
        ):
            send_started.set()
            allow_completion.wait(timeout=5)
            return True

    try:
        section = ComposeSection(
            root,
            view_model=ComposeViewModel(
                ControlledComposer()
            ),
        )

        fill_compose_fields(section)
        section.send_button.invoke()

        assert send_started.wait(timeout=1)

        poll_id = section._send_poll_id

        assert poll_id is not None

        section.destroy()

        assert section._send_poll_id is None
        assert poll_id not in root.tk.call(
            "after",
            "info",
        )

    finally:
        allow_completion.set()
        root.destroy()


def test_compose_section_sets_recipient_from_contact():
    import tkinter as tk
    from tkinter import ttk

    from garlicsmtp.gui.tk_compose_section import (
        ComposeSection,
    )

    root = tk.Tk()
    root.withdraw()

    try:
        section = ComposeSection.__new__(ComposeSection)
        ttk.Frame.__init__(section, root)

        section._send_poll_id = None

        section.recipient_input = ttk.Entry(section)

        section.recipient_input.insert(
            0,
            "old@example.com",
        )

        section.set_recipient_from_contact(
            "alice@example.com",
        )

        assert (
            section.recipient_input.get()
            == "alice@example.com"
        )

    finally:
        root.destroy()


def test_compose_section_has_select_contact_button():
    import inspect

    from garlicsmtp.gui.tk_compose_section import (
        ComposeSection,
    )

    source = inspect.getsource(ComposeSection.__init__)

    assert "self.select_contact_button = ttk.Button(" in source
    assert 'text="Select Contact"' in source
    assert "command=self._select_contact" in source
    assert "self.select_contact_button.grid(" in source


def test_compose_section_accepts_contacts_view_model():
    root = tk.Tk()
    root.withdraw()

    try:
        class FakeContactsViewModel:
            contacts = [
                {
                    "id": 1,
                    "name": "Alice",
                    "onion_address": "alice@example.onion",
                },
            ]

        contacts_view_model = FakeContactsViewModel()

        section = ComposeSection(
            root,
            view_model=ComposeViewModel(
                FakeComposer()
            ),
            contacts_view_model=contacts_view_model,
        )

        assert (
            section.contacts_view_model
            is contacts_view_model
        )

    finally:
        root.destroy()


def test_select_contact_opens_toplevel(monkeypatch):
    from tkinter import ttk

    created_windows = []

    class FakeContactWindow:
        def __init__(self, master):
            self.master = master
            created_windows.append(self)

        def title(self, value):
            self.window_title = value

        def geometry(self, value):
            self.window_geometry = value

        def columnconfigure(self, index, weight):
            pass

        def rowconfigure(self, index, weight):
            pass

    monkeypatch.setattr(
        compose_module.tk,
        "Toplevel",
        FakeContactWindow,
    )

    class FakeTreeview:
        def __init__(self, master, **kwargs):
            pass

        def heading(self, column, text):
            pass

        def column(self, column, width):
            pass

        def grid(self, **kwargs):
            pass

        def insert(self, *args, **kwargs):
            pass

        def bind(self, sequence, callback):
            pass

        def get_children(self):
            return ()

        def delete(self, item):
            pass

    monkeypatch.setattr(
        compose_module.ttk,
        "Treeview",
        FakeTreeview,
    )

    class FakeButton:
        def __init__(self, master, **kwargs):
            pass

        def grid(self, **kwargs):
            pass

    monkeypatch.setattr(
        compose_module.ttk,
        "Button",
        FakeButton,
    )

    class FakeLabel:
        def __init__(self, master, **kwargs):
            pass

        def grid(self, **kwargs):
            pass


    class FakeEntry:
        def __init__(self, master, **kwargs):
            pass

        def grid(self, **kwargs):
            pass


    monkeypatch.setattr(
        compose_module.ttk,
        "Label",
        FakeLabel,
    )

    monkeypatch.setattr(
        compose_module.ttk,
        "Entry",
        FakeEntry,
    )

    root = tk.Tk()
    root.withdraw()

    try:
        section = ComposeSection.__new__(ComposeSection)
        ttk.Frame.__init__(section, root)

        section._send_poll_id = None
        class FakeContactsViewModel:
            def refresh(self):
                pass

            contacts = []

        section.contacts_view_model = FakeContactsViewModel()

        created_windows.clear()

        section._select_contact()

        assert len(created_windows) == 1
        assert (
            created_windows[0].window_title
            == "Select Contact"
        )

    finally:
        root.destroy()


def test_select_contact_displays_saved_contacts():
    root = tk.Tk()
    root.withdraw()

    try:
        class FakeContactsViewModel:
            def refresh(self):
                pass

            contacts = [
                {
                    "id": 1,
                    "name": "Alice",
                    "onion_address": "alice@example.onion",
                },
                {
                    "id": 2,
                    "name": "Bob",
                    "onion_address": "bob@example.onion",
                },
            ]

        section = ComposeSection(
            root,
            view_model=ComposeViewModel(
                FakeComposer()
            ),
            contacts_view_model=FakeContactsViewModel(),
        )

        section._select_contact()

        tree = section.contact_selector_tree

        assert len(tree.get_children()) == 2

        assert tree.item(
            "1",
            "values",
        ) == (
            "Alice",
            "alice@example.onion",
        )

        assert tree.item(
            "2",
            "values",
        ) == (
            "Bob",
            "bob@example.onion",
        )

    finally:
        root.destroy()


def test_select_contact_applies_selected_address():
    root = tk.Tk()
    root.withdraw()

    try:
        class FakeContactsViewModel:
            def refresh(self):
                pass

            contacts = [
                {
                    "id": 1,
                    "name": "Alice",
                    "onion_address": "alice@example.onion",
                },
            ]

        section = ComposeSection(
            root,
            view_model=ComposeViewModel(
                FakeComposer()
            ),
            contacts_view_model=FakeContactsViewModel(),
        )

        section.recipient_input.insert(
            0,
            "previous@example.onion",
        )

        section._select_contact()

        selector_window = (
            section.contact_selector_tree.winfo_toplevel()
        )

        section.contact_selector_tree.selection_set("1")

        section._apply_selected_contact()

        assert (
            section.recipient_input.get()
            == "alice@example.onion"
        )

        assert not selector_window.winfo_exists()

    finally:
        root.destroy()


def test_select_contact_without_selection_preserves_recipient():
    root = tk.Tk()
    root.withdraw()

    try:
        class FakeContactsViewModel:
            def refresh(self):
                pass

            contacts = [
                {
                    "id": 1,
                    "name": "Alice",
                    "onion_address": "alice@example.onion",
                },
            ]

        section = ComposeSection(
            root,
            view_model=ComposeViewModel(
                FakeComposer()
            ),
            contacts_view_model=FakeContactsViewModel(),
        )

        section.recipient_input.insert(
            0,
            "previous@example.onion",
        )

        section._select_contact()

        selector_window = (
            section.contact_selector_tree.winfo_toplevel()
        )

        section.contact_selector_tree.selection_remove(
            section.contact_selector_tree.selection()
        )

        section._apply_selected_contact()

        assert (
            section.recipient_input.get()
            == "previous@example.onion"
        )

        assert selector_window.winfo_exists()

    finally:
        root.destroy()


def test_select_contact_double_click_applies_address():
    root = tk.Tk()
    root.withdraw()

    try:
        class FakeContactsViewModel:
            def refresh(self):
                pass

            contacts = [
                {
                    "id": 1,
                    "name": "Alice",
                    "onion_address": "alice@example.onion",
                },
            ]

        section = ComposeSection(
            root,
            view_model=ComposeViewModel(
                FakeComposer()
            ),
            contacts_view_model=FakeContactsViewModel(),
        )

        section._select_contact()

        tree = section.contact_selector_tree
        selector_window = tree.winfo_toplevel()

        tree.selection_set("1")

        binding = tree.bind("<Double-1>")

        assert binding
        assert "_apply_selected_contact" in binding or "lambda" in binding

    finally:
        root.destroy()


def test_select_contact_refreshes_contacts_before_display():
    root = tk.Tk()
    root.withdraw()

    try:
        class FakeContactsViewModel:
            def __init__(self):
                self.contacts = []
                self.refresh_called = False

            def refresh(self):
                self.refresh_called = True
                self.contacts = [
                    {
                        "id": 1,
                        "name": "Alice",
                        "onion_address": "alice@example.onion",
                    },
                ]

        contacts_view_model = FakeContactsViewModel()

        section = ComposeSection(
            root,
            view_model=ComposeViewModel(
                FakeComposer()
            ),
            contacts_view_model=contacts_view_model,
        )

        section._select_contact()

        assert contacts_view_model.refresh_called

        assert section.contact_selector_tree.item(
            "1",
            "values",
        ) == (
            "Alice",
            "alice@example.onion",
        )

    finally:
        root.destroy()


def test_select_contact_with_empty_address_book():
    root = tk.Tk()
    root.withdraw()

    try:
        class FakeContactsViewModel:
            def __init__(self):
                self.contacts = []

            def refresh(self):
                pass

        section = ComposeSection(
            root,
            view_model=ComposeViewModel(
                FakeComposer()
            ),
            contacts_view_model=FakeContactsViewModel(),
        )

        section.recipient_input.insert(
            0,
            "previous@example.onion",
        )

        section._select_contact()

        assert section.contact_selector_tree.get_children() == ()

        section._apply_selected_contact()

        assert (
            section.recipient_input.get()
            == "previous@example.onion"
        )

        assert (
            section.contact_selector_tree
            .winfo_toplevel()
            .winfo_exists()
        )

    finally:
        root.destroy()


def test_select_contact_without_contacts_view_model_does_nothing():
    root = tk.Tk()
    root.withdraw()

    try:
        section = ComposeSection(
            root,
            view_model=ComposeViewModel(
                FakeComposer()
            ),
        )

        section.recipient_input.insert(
            0,
            "previous@example.onion",
        )

        section._select_contact()

        assert (
            section.recipient_input.get()
            == "previous@example.onion"
        )

        assert not hasattr(
            section,
            "contact_selector_tree",
        )

    finally:
        root.destroy()


def test_compose_section_has_recipient_contact_label():
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
            "recipient_contact_label",
        )

        assert (
            section.recipient_contact_label.cget("text")
            == ""
        )

    finally:
        root.destroy()


def test_compose_section_displays_saved_recipient_name():
    root = tk.Tk()
    root.withdraw()

    try:
        class FakeContactsViewModel:
            def get_contact_name(self, onion_address):
                if onion_address == "mario@example.onion":
                    return "Mario Rossi"

                return None

        section = ComposeSection(
            root,
            view_model=ComposeViewModel(
                FakeComposer()
            ),
            contacts_view_model=FakeContactsViewModel(),
        )

        section.recipient_input.insert(
            0,
            "mario@example.onion",
        )

        section._update_recipient_contact_label()

        assert (
            section.recipient_contact_label.cget("text")
            == "Contatto: Mario Rossi"
        )

        assert (
            section.recipient_input.get()
            == "mario@example.onion"
        )

    finally:
        root.destroy()


def test_compose_section_updates_contact_name_on_key_release():
    root = tk.Tk()
    root.withdraw()

    try:
        class FakeContactsViewModel:
            def get_contact_name(self, onion_address):
                if onion_address == "mario@example.onion":
                    return "Mario Rossi"

                return None

        section = ComposeSection(
            root,
            view_model=ComposeViewModel(
                FakeComposer()
            ),
            contacts_view_model=FakeContactsViewModel(),
        )

        section.recipient_input.insert(
            0,
            "mario@example.onion",
        )

        binding = section.recipient_input.bind(
            "<KeyRelease>"
        )

        assert binding

        section._update_recipient_contact_label()

        assert (
            section.recipient_contact_label.cget("text")
            == "Contatto: Mario Rossi"
        )

        assert (
            section.recipient_input.get()
            == "mario@example.onion"
        )

    finally:
        root.destroy()


def test_compose_section_updates_contact_name_after_selection():
    root = tk.Tk()
    root.withdraw()

    try:
        class FakeContactsViewModel:
            def get_contact_name(self, onion_address):
                if onion_address == "mario@example.onion":
                    return "Mario Rossi"
                return None

        section = ComposeSection(
            root,
            view_model=ComposeViewModel(FakeComposer()),
            contacts_view_model=FakeContactsViewModel(),
        )

        section.set_recipient_from_contact(
            "mario@example.onion"
        )

        assert (
            section.recipient_input.get()
            == "mario@example.onion"
        )

        assert (
            section.recipient_contact_label.cget("text")
            == "Contatto: Mario Rossi"
        )

    finally:
        root.destroy()


def test_compose_section_clear_removes_recipient_contact_name():
    root = tk.Tk()
    root.withdraw()

    try:
        class FakeContactsViewModel:
            def get_contact_name(self, onion_address):
                if onion_address == "mario@example.onion":
                    return "Mario Rossi"
                return None

        section = ComposeSection(
            root,
            view_model=ComposeViewModel(FakeComposer()),
            contacts_view_model=FakeContactsViewModel(),
        )

        section.set_recipient_from_contact(
            "mario@example.onion"
        )

        assert (
            section.recipient_contact_label.cget("text")
            == "Contatto: Mario Rossi"
        )

        section._clear_fields()

        assert section.recipient_input.get() == ""
        assert section.recipient_contact_label.cget("text") == ""

    finally:
        root.destroy()


def test_select_contact_filters_by_search_text():
    root = tk.Tk()
    root.withdraw()

    try:
        class FakeContactsViewModel:
            contacts = [
                {
                    "id": 1,
                    "name": "Mario Rossi",
                    "onion_address": "mario@example.onion",
                },
                {
                    "id": 2,
                    "name": "Luigi Verdi",
                    "onion_address": "luigi@example.onion",
                },
            ]

            def refresh(self):
                pass

            def filter_contacts(self, query):
                normalized = query.casefold()
                return [
                    contact
                    for contact in self.contacts
                    if (
                        normalized in contact["name"].casefold()
                        or normalized
                        in contact["onion_address"].casefold()
                    )
                ]

        contacts_view_model = FakeContactsViewModel()

        section = ComposeSection(
            root,
            view_model=ComposeViewModel(
                FakeComposer()
            ),
            contacts_view_model=contacts_view_model,
        )

        section.recipient_input.insert(
            0,
            "previous@example.onion",
        )

        section._select_contact()

        tree = section.contact_selector_tree

        assert len(tree.get_children()) == 2

        section.contact_search_var.set("mario")

        rows = tree.get_children()

        assert len(rows) == 1

        assert tree.item(
            rows[0],
            "values",
        ) == (
            "Mario Rossi",
            "mario@example.onion",
        )

        assert len(contacts_view_model.contacts) == 2

        assert (
            section.recipient_input.get()
            == "previous@example.onion"
        )

    finally:
        root.destroy()


def test_select_contact_filters_by_onion_address():
    root = tk.Tk()
    root.withdraw()

    try:
        class FakeContactsViewModel:
            contacts = [
                {
                    "id": 1,
                    "name": "Mario Rossi",
                    "onion_address": "mario@example.onion",
                },
                {
                    "id": 2,
                    "name": "Luigi Verdi",
                    "onion_address": "luigi@example.onion",
                },
            ]

            def refresh(self):
                pass

            def filter_contacts(self, query):
                normalized = query.casefold()
                return [
                    contact
                    for contact in self.contacts
                    if (
                        normalized in contact["name"].casefold()
                        or normalized
                        in contact["onion_address"].casefold()
                    )
                ]

        section = ComposeSection(
            root,
            view_model=ComposeViewModel(FakeComposer()),
            contacts_view_model=FakeContactsViewModel(),
        )

        section._select_contact()

        tree = section.contact_selector_tree

        section.contact_search_var.set("LUIGI@")

        rows = tree.get_children()

        assert len(rows) == 1
        assert tree.item(rows[0], "values") == (
            "Luigi Verdi",
            "luigi@example.onion",
        )

        section.contact_search_var.set("")

        assert len(tree.get_children()) == 2

    finally:
        root.destroy()