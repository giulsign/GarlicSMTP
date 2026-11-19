
# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import tkinter as tk

import pytest

from garlicsmtp.gui.contacts_repository import (
    ContactsRepository,
)
from garlicsmtp.gui.contacts_view_model import (
    ContactsViewModel,
)


@pytest.fixture
def root():
    try:
        window = tk.Tk()
    except tk.TclError:
        pytest.skip(
            "Tkinter display unavailable"
        )

    window.withdraw()

    try:
        yield window
    finally:
        window.destroy()


@pytest.fixture
def view_model(tmp_path):
    repository = ContactsRepository(
        tmp_path / "contacts.json"
    )

    return ContactsViewModel(
        repository
    )


def test_contacts_section_initial_widgets(
    root,
    view_model,
):
    from garlicsmtp.gui.tk_contacts_section import (
        ContactsSection,
    )

    section = ContactsSection(
        root,
        view_model=view_model,
    )

    assert section.title == "Contacts"

    assert section.contacts_tree["columns"] == (
        "name",
        "onion_address",
    )

    assert section.name_entry is not None
    assert section.address_entry is not None

    assert section.add_button["text"] == "Add"
    assert section.update_button["text"] == "Update"
    assert section.delete_button["text"] == "Delete"
    assert section.refresh_button["text"] == "Refresh"

    section.destroy()


def test_contacts_section_displays_existing_contacts(
    root,
    view_model,
):
    from garlicsmtp.gui.tk_contacts_section import (
        ContactsSection,
    )

    view_model.add_contact(
        name="Mario",
        onion_address="mario@example.onion",
    )

    section = ContactsSection(
        root,
        view_model=view_model,
    )

    rows = section.contacts_tree.get_children()

    assert len(rows) == 1

    assert section.contacts_tree.item(
        rows[0],
        "values",
    ) == (
        "Mario",
        "mario@example.onion",
    )

    section.destroy()



def test_select_contact_populates_fields(
    root,
    view_model,
):
    from garlicsmtp.gui.tk_contacts_section import (
        ContactsSection,
    )

    view_model.add_contact(
        name="Mario",
        onion_address="mario@example.onion",
    )

    section = ContactsSection(
        root,
        view_model=view_model,
    )

    section.contacts_tree.selection_set("1")
    section.contacts_tree.event_generate(
        "<<TreeviewSelect>>"
    )

    assert section.name_var.get() == "Mario"
    assert section.address_var.get() == (
        "mario@example.onion"
    )

    section.destroy()


def test_add_button_creates_contact(
    root,
    view_model,
):
    from garlicsmtp.gui.tk_contacts_section import (
        ContactsSection,
    )

    section = ContactsSection(
        root,
        view_model=view_model,
    )

    section.name_var.set("Luigi")
    section.address_var.set(
        "luigi@example.onion"
    )

    section.add_button.invoke()

    assert len(view_model.contacts) == 1
    assert view_model.contacts[0]["name"] == "Luigi"

    assert len(
        section.contacts_tree.get_children()
    ) == 1

    assert section.name_var.get() == ""
    assert section.address_var.get() == ""

    section.destroy()


def test_update_button_modifies_selected_contact(
    root,
    view_model,
):
    from garlicsmtp.gui.tk_contacts_section import (
        ContactsSection,
    )

    view_model.add_contact(
        name="Mario",
        onion_address="mario@example.onion",
    )

    section = ContactsSection(
        root,
        view_model=view_model,
    )

    section.contacts_tree.selection_set("1")

    section.name_var.set("Mario Rossi")
    section.address_var.set(
        "mario.rossi@example.onion"
    )

    section.update_button.invoke()

    assert view_model.contacts[0]["name"] == (
        "Mario Rossi"
    )

    assert view_model.contacts[0][
        "onion_address"
    ] == "mario.rossi@example.onion"

    section.destroy()


def test_delete_button_removes_selected_contact(
    root,
    view_model,
    monkeypatch,
):
    from garlicsmtp.gui.tk_contacts_section import (
        ContactsSection,
    )

    from garlicsmtp.gui import (
        tk_contacts_section,
    )

    monkeypatch.setattr(
        tk_contacts_section.messagebox,
        "askyesno",
        lambda *args, **kwargs: True,
    )

    view_model.add_contact(
        name="Mario",
        onion_address="mario@example.onion",
    )

    section = ContactsSection(
        root,
        view_model=view_model,
    )

    section.contacts_tree.selection_set("1")
    section.delete_button.invoke()

    assert view_model.contacts == []

    assert (
        section.contacts_tree.get_children()
        == ()
    )

    section.destroy()


def test_refresh_button_loads_external_changes(
    root,
    view_model,
):
    from garlicsmtp.gui.tk_contacts_section import (
        ContactsSection,
    )

    section = ContactsSection(
        root,
        view_model=view_model,
    )

    view_model.repository.add_contact(
        name="Anna",
        onion_address="anna@example.onion",
    )

    section.refresh_button.invoke()

    rows = section.contacts_tree.get_children()

    assert len(rows) == 1

    assert section.contacts_tree.item(
        rows[0],
        "values",
    ) == (
        "Anna",
        "anna@example.onion",
    )

    section.destroy()



def test_delete_cancelled_preserves_contact(
    root,
    view_model,
    monkeypatch,
):
    from garlicsmtp.gui.tk_contacts_section import (
        ContactsSection,
    )
    from garlicsmtp.gui import tk_contacts_section

    monkeypatch.setattr(
        tk_contacts_section.messagebox,
        "askyesno",
        lambda *args, **kwargs: False,
    )

    view_model.add_contact(
        name="Mario",
        onion_address="mario@example.onion",
    )

    section = ContactsSection(
        root,
        view_model=view_model,
    )

    section.contacts_tree.selection_set("1")
    section.delete_button.invoke()

    assert len(view_model.contacts) == 1
    assert view_model.contacts[0]["name"] == "Mario"
    assert len(
        section.contacts_tree.get_children()
    ) == 1

    section.destroy()


def test_update_without_selection_preserves_contacts(
    root,
    view_model,
):
    from garlicsmtp.gui.tk_contacts_section import (
        ContactsSection,
    )

    view_model.add_contact(
        name="Mario",
        onion_address="mario@example.onion",
    )

    section = ContactsSection(
        root,
        view_model=view_model,
    )

    section.name_var.set("Luigi")
    section.address_var.set(
        "luigi@example.onion"
    )

    section.update_button.invoke()

    assert view_model.contacts[0]["name"] == "Mario"

    section.destroy()


def test_delete_without_selection_preserves_contacts(
    root,
    view_model,
    monkeypatch,
):
    from garlicsmtp.gui.tk_contacts_section import (
        ContactsSection,
    )
    from garlicsmtp.gui import tk_contacts_section

    def unexpected_confirmation(*args, **kwargs):
        pytest.fail(
            "Confirmation must not open without selection"
        )

    monkeypatch.setattr(
        tk_contacts_section.messagebox,
        "askyesno",
        unexpected_confirmation,
    )

    view_model.add_contact(
        name="Mario",
        onion_address="mario@example.onion",
    )

    section = ContactsSection(
        root,
        view_model=view_model,
    )

    section.delete_button.invoke()

    assert len(view_model.contacts) == 1

    section.destroy()


def test_invalid_add_shows_error_without_creating_contact(
    root,
    view_model,
    monkeypatch,
):
    from garlicsmtp.gui.tk_contacts_section import (
        ContactsSection,
    )
    from garlicsmtp.gui import tk_contacts_section

    errors = []

    monkeypatch.setattr(
        tk_contacts_section.messagebox,
        "showerror",
        lambda *args, **kwargs: errors.append(
            (args, kwargs)
        ),
    )

    section = ContactsSection(
        root,
        view_model=view_model,
    )

    section.name_var.set("")
    section.address_var.set(
        "mario@example.onion"
    )

    section.add_button.invoke()

    assert view_model.contacts == []
    assert len(errors) == 1

    assert section.name_var.get() == ""
    assert section.address_var.get() == (
        "mario@example.onion"
    )

    section.destroy()


def test_failed_refresh_preserves_displayed_contacts(
    root,
    view_model,
    monkeypatch,
):
    from garlicsmtp.gui.tk_contacts_section import (
        ContactsSection,
    )
    from garlicsmtp.gui import tk_contacts_section

    errors = []

    monkeypatch.setattr(
        tk_contacts_section.messagebox,
        "showerror",
        lambda *args, **kwargs: errors.append(
            (args, kwargs)
        ),
    )

    view_model.add_contact(
        name="Mario",
        onion_address="mario@example.onion",
    )

    section = ContactsSection(
        root,
        view_model=view_model,
    )

    def failing_refresh():
        raise ValueError(
            "Invalid contacts JSON"
        )

    monkeypatch.setattr(
        view_model,
        "refresh",
        failing_refresh,
    )

    section.refresh_button.invoke()

    rows = section.contacts_tree.get_children()

    assert len(rows) == 1
    assert section.contacts_tree.item(
        rows[0],
        "values",
    ) == (
        "Mario",
        "mario@example.onion",
    )

    assert len(errors) == 1

    section.destroy()



def test_main_window_accepts_contacts_view_model():
    import inspect

    from garlicsmtp.gui.tk_main_window import (
        MainWindow,
    )

    signature = inspect.signature(
        MainWindow.__init__
    )

    assert (
        "contacts_view_model"
        in signature.parameters
    )



def test_main_window_creates_contacts_section_on_demand():
    import inspect

    from garlicsmtp.gui.tk_main_window import (
        MainWindow,
    )

    constructor_source = inspect.getsource(
        MainWindow.__init__
    )

    open_source = inspect.getsource(
        MainWindow._open_contacts_window
    )

    assert "ContactsSection(" not in constructor_source

    assert "ContactsSection(" in open_source

    assert "self.contacts_view_model" in open_source


def test_run_gui_source_wires_contacts_repository():
    import inspect

    from garlicsmtp.gui.application import (
        run_gui,
    )

    source = inspect.getsource(run_gui)

    assert "ContactsRepository(" in source
    assert "ContactsViewModel(" in source
    assert "application_paths.contacts_file" in source
    assert "contacts_view_model=" in source



def test_contacts_view_model_uses_application_contacts_file(
    tmp_path,
):
    from garlicsmtp.configuration import (
        ApplicationPaths,
    )
    from garlicsmtp.gui.contacts_repository import (
        ContactsRepository,
    )
    from garlicsmtp.gui.contacts_view_model import (
        ContactsViewModel,
    )

    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )

    repository = ContactsRepository(
        paths.contacts_file
    )

    view_model = ContactsViewModel(
        repository
    )

    view_model.add_contact(
        name="Mario",
        onion_address="mario@example.onion",
    )

    assert paths.contacts_file.exists()

    reloaded = ContactsViewModel(
        ContactsRepository(
            paths.contacts_file
        )
    )

    assert len(reloaded.contacts) == 1
    assert reloaded.contacts[0]["name"] == "Mario"
    assert reloaded.contacts[0][
        "onion_address"
    ] == "mario@example.onion"


def test_main_window_exposes_open_contacts_window():
    from garlicsmtp.gui.tk_main_window import (
        MainWindow,
    )

    assert callable(
        getattr(
            MainWindow,
            "_open_contacts_window",
            None,
        )
    )


def test_open_contacts_window_creates_toplevel(
    root,
    view_model,
    monkeypatch,
):
    import tkinter as tk

    from garlicsmtp.gui import tk_main_window

    created_windows = []
    created_sections = []

    class FakeContactsWindow:
        def __init__(self, master):
            self.master = master
            created_windows.append(self)

        def title(self, value):
            self.window_title = value

        def geometry(self, value):
            self.window_geometry = value

        def protocol(self, name, callback):
            self.close_protocol = name
            self.close_callback = callback

        def columnconfigure(self, *args, **kwargs):
            pass

        def rowconfigure(self, *args, **kwargs):
            pass

        def destroy(self):
            self.destroyed = True

    class FakeContactsSection:
        def __init__(self, master, *, view_model):
            self.master = master
            self.view_model = view_model
            created_sections.append(self)

        def grid(self, **kwargs):
            self.grid_options = kwargs

        def refresh_view(self):
            pass

    monkeypatch.setattr(
        tk_main_window.tk,
        "Toplevel",
        FakeContactsWindow,
    )

    monkeypatch.setattr(
        tk_main_window,
        "ContactsSection",
        FakeContactsSection,
    )

    window = tk_main_window.MainWindow.__new__(
        tk_main_window.MainWindow
    )

    tk.ttk.Frame.__init__(
        window,
        root,
    )

    contacts_view_model = object()

    window.contacts_view_model = contacts_view_model
    window.contacts_section = None
    window._contacts_window = None

    window._open_contacts_window()

    assert len(created_windows) == 1
    assert len(created_sections) == 1

    assert (
        created_sections[0].master
        is created_windows[0]
    )

    assert (
        created_sections[0].view_model
        is contacts_view_model
    )

    assert (
        created_windows[0].window_title
        == "Contacts"
    )

    assert (
        created_windows[0].close_protocol
        == "WM_DELETE_WINDOW"
    )


def test_open_contacts_window_reuses_existing_window(
    root,
    monkeypatch,
):
    import tkinter as tk

    from tkinter import ttk
    from garlicsmtp.gui import tk_main_window

    created_windows = []

    class FakeContactsWindow:
        def __init__(self, master):
            self.master = master
            self.destroyed = False
            self.lift_calls = 0
            self.focus_calls = 0
            created_windows.append(self)

        def title(self, value):
            pass

        def geometry(self, value):
            pass

        def columnconfigure(self, *args, **kwargs):
            pass

        def rowconfigure(self, *args, **kwargs):
            pass

        def protocol(self, name, callback):
            self.close_callback = callback

        def winfo_exists(self):
            return not self.destroyed

        def lift(self):
            self.lift_calls += 1

        def focus_set(self):
            self.focus_calls += 1

        def destroy(self):
            self.destroyed = True

    class FakeContactsSection:
        def __init__(self, master, *, view_model):
            self.master = master

        def grid(self, **kwargs):
            pass

    monkeypatch.setattr(
        tk_main_window.tk,
        "Toplevel",
        FakeContactsWindow,
    )

    monkeypatch.setattr(
        tk_main_window,
        "ContactsSection",
        FakeContactsSection,
    )

    window = tk_main_window.MainWindow.__new__(
        tk_main_window.MainWindow
    )

    ttk.Frame.__init__(
        window,
        root,
    )

    window.contacts_view_model = object()
    window.contacts_section = None
    window._contacts_window = None

    window._open_contacts_window()
    window._open_contacts_window()

    assert len(created_windows) == 1
    assert created_windows[0].lift_calls == 1
    assert created_windows[0].focus_calls == 1


def test_contacts_window_can_reopen_after_close(
    root,
    monkeypatch,
):
    from tkinter import ttk

    from garlicsmtp.gui import tk_main_window

    created_windows = []

    class FakeContactsWindow:
        def __init__(self, master):
            self.master = master
            self.destroyed = False
            created_windows.append(self)

        def title(self, value):
            pass

        def geometry(self, value):
            pass

        def columnconfigure(self, *args, **kwargs):
            pass

        def rowconfigure(self, *args, **kwargs):
            pass

        def protocol(self, name, callback):
            assert name == "WM_DELETE_WINDOW"
            self.close_callback = callback

        def winfo_exists(self):
            return not self.destroyed

        def destroy(self):
            self.destroyed = True

    class FakeContactsSection:
        def __init__(self, master, *, view_model):
            self.master = master
            self.view_model = view_model

        def grid(self, **kwargs):
            pass

    monkeypatch.setattr(
        tk_main_window.tk,
        "Toplevel",
        FakeContactsWindow,
    )

    monkeypatch.setattr(
        tk_main_window,
        "ContactsSection",
        FakeContactsSection,
    )

    window = tk_main_window.MainWindow.__new__(
        tk_main_window.MainWindow
    )

    ttk.Frame.__init__(
        window,
        root,
    )

    window.contacts_view_model = object()
    window.contacts_section = None
    window._contacts_window = None

    window._open_contacts_window()

    first_window = window._contacts_window

    assert len(created_windows) == 1

    first_window.close_callback()

    assert first_window.destroyed is True

    window._open_contacts_window()

    assert len(created_windows) == 2

    assert window._contacts_window is created_windows[1]

    assert created_windows[1] is not first_window


def test_main_window_does_not_embed_contacts_in_dashboard():
    import inspect

    from garlicsmtp.gui.tk_main_window import (
        MainWindow,
    )

    source = inspect.getsource(
        MainWindow.__init__
    )

    assert "ContactsSection(" not in source
    assert "self.contacts_section.grid(" not in source


def test_main_window_has_contacts_button():
    import inspect

    from garlicsmtp.gui.tk_main_window import (
        MainWindow,
    )

    source = inspect.getsource(
        MainWindow.__init__
    )

    assert "self.contacts_button = ttk.Button(" in source
    assert 'text="Contacts"' in source
    assert "command=self._open_contacts_window" in source
    assert "self.contacts_button.grid(" in source


def test_main_window_close_destroys_contacts_window(
    root,
    monkeypatch,
):
    from tkinter import ttk
    from garlicsmtp.gui.tk_main_window import MainWindow

    events = []

    class FakeContactsWindow:
        def winfo_exists(self):
            return True

        def destroy(self):
            events.append("contacts_destroy")

    class FakeViewModel:
        is_running = False

        def unsubscribe(self, callback):
            events.append("unsubscribe")

        def close(self):
            events.append("view_model_close")

    window = MainWindow.__new__(MainWindow)
    ttk.Frame.__init__(window, root)

    window.view_model = FakeViewModel()
    window.compose_section = None
    window._contacts_window = FakeContactsWindow()
    window._refresh_poll_after_id = None
    window._queue_refresh = lambda: None

    assert window.close() is True

    assert events == [
        "contacts_destroy",
        "unsubscribe",
        "view_model_close",
    ]

def test_main_window_passes_contacts_view_model_to_compose():
    import inspect

    from garlicsmtp.gui.tk_main_window import MainWindow

    source = inspect.getsource(MainWindow.__init__)

    assert (
        "self.compose_section = ComposeSection("
        in source
    )

    assert (
        "view_model=self.view_model.compose,"
        in source
    )

    assert (
        "contacts_view_model=self.contacts_view_model,"
        in source
    )


def test_contacts_section_filters_by_search_text(
    root,
    view_model,
):
    from garlicsmtp.gui.tk_contacts_section import (
        ContactsSection,
    )

    view_model.add_contact(
        name="Mario Rossi",
        onion_address="mario@example.onion",
    )

    view_model.add_contact(
        name="Luigi Verdi",
        onion_address="luigi@example.onion",
    )

    section = ContactsSection(
        root,
        view_model=view_model,
    )

    try:
        assert len(
            section.contacts_tree.get_children()
        ) == 2

        section.search_var.set("mario")

        rows = section.contacts_tree.get_children()

        assert len(rows) == 1

        assert section.contacts_tree.item(
            rows[0],
            "values",
        ) == (
            "Mario Rossi",
            "mario@example.onion",
        )

        assert len(view_model.contacts) == 2

    finally:
        section.destroy()


def test_contacts_section_clearing_search_restores_all_contacts(
    root,
    view_model,
):
    from garlicsmtp.gui.tk_contacts_section import (
        ContactsSection,
    )

    view_model.add_contact(
        name="Mario Rossi",
        onion_address="mario@example.onion",
    )

    view_model.add_contact(
        name="Luigi Verdi",
        onion_address="luigi@example.onion",
    )

    section = ContactsSection(
        root,
        view_model=view_model,
    )

    try:
        section.search_var.set("mario")

        assert len(
            section.contacts_tree.get_children()
        ) == 1

        section.search_var.set("")

        rows = section.contacts_tree.get_children()

        assert len(rows) == 2
        assert len(view_model.contacts) == 2

    finally:
        section.destroy()


def test_contacts_section_filters_by_onion_address(
    root,
    view_model,
):
    from garlicsmtp.gui.tk_contacts_section import (
        ContactsSection,
    )

    view_model.add_contact(
        name="Mario Rossi",
        onion_address="mario@alpha.onion",
    )

    view_model.add_contact(
        name="Luigi Verdi",
        onion_address="luigi@beta.onion",
    )

    section = ContactsSection(
        root,
        view_model=view_model,
    )

    try:
        section.search_var.set("BETA.ONION")

        rows = section.contacts_tree.get_children()

        assert len(rows) == 1

        assert section.contacts_tree.item(
            rows[0],
            "values",
        ) == (
            "Luigi Verdi",
            "luigi@beta.onion",
        )

        assert len(view_model.contacts) == 2

    finally:
        section.destroy()