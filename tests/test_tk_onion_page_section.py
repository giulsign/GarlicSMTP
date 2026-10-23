# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import pytest

from garlicsmtp.gui.tk_onion_page_section import (
    OnionPageSection,
)


def test_onion_page_section_saves_selected_page():
    calls = []

    class FakePreferences:
        def save(self, *, enabled, html_path):
            calls.append((enabled, html_path))

    section = OnionPageSection.__new__(OnionPageSection)
    section.preferences = FakePreferences()

    section.save_selection(
        enabled=True,
        html_path="pages/personal.html",
    )

    assert calls == [(True, "pages/personal.html")]


def test_onion_page_section_saves_default_page():
    calls = []

    class FakePreferences:
        def save(self, *, enabled, html_path):
            calls.append((enabled, html_path))

    section = OnionPageSection.__new__(OnionPageSection)
    section.preferences = FakePreferences()

    section.save_selection(
        enabled=False,
        html_path="",
    )

    assert calls == [(False, "")]


def test_onion_page_section_loads_existing_preferences():
    class FakePreferences:
        def load(self):
            return True, "pages/personal.html"

    section = OnionPageSection.__new__(OnionPageSection)
    section.preferences = FakePreferences()

    enabled, html_path = section.load_selection()

    assert enabled is True
    assert html_path == "pages/personal.html"


def test_onion_page_section_loads_default_preferences():
    class FakePreferences:
        def load(self):
            return False, ""

    section = OnionPageSection.__new__(OnionPageSection)
    section.preferences = FakePreferences()

    assert section.load_selection() == (False, "")


def test_onion_page_section_reports_load_error():
    class FakePreferences:
        def load(self):
            raise ValueError("Invalid Onion configuration")

    section = OnionPageSection.__new__(OnionPageSection)
    section.preferences = FakePreferences()

    with pytest.raises(
        ValueError,
        match="Invalid Onion configuration",
    ):
        section.load_selection()


def test_onion_page_section_rejects_save_after_load_failure():
    calls = []

    class FakePreferences:
        def save(self, *, enabled, html_path):
            calls.append((enabled, html_path))

    section = OnionPageSection.__new__(OnionPageSection)
    section.preferences = FakePreferences()
    section._preferences_load_failed = True

    with pytest.raises(
        RuntimeError,
        match="configuration",
    ):
        section.save_selection(
            enabled=False,
            html_path="",
        )

    assert calls == []


def test_onion_page_section_initializes_failed_load_state():
    class FakePreferences:
        def load(self):
            return False, ""

    section = OnionPageSection.__new__(OnionPageSection)
    section.preferences = FakePreferences()
    section._preferences_load_failed = True

    section._load_initial_selection()

    assert section._preferences_load_failed is False


def test_onion_page_section_marks_failed_initial_load():
    class FakePreferences:
        def load(self):
            raise ValueError("Invalid Onion configuration")

    section = OnionPageSection.__new__(OnionPageSection)
    section.preferences = FakePreferences()
    section._preferences_load_failed = False

    with pytest.raises(
        ValueError,
        match="Invalid Onion configuration",
    ):
        section._load_initial_selection()

    assert section._preferences_load_failed is True


def test_onion_page_section_constructor_uses_protected_loader():
    import inspect

    source = inspect.getsource(OnionPageSection.__init__)

    assert "self._try_load_initial_selection()" in source
    assert "self.load_selection()" not in source


def test_onion_page_section_constructor_does_not_bypass_protected_loader():
    import inspect

    source = inspect.getsource(OnionPageSection.__init__)

    assert "self.load_selection()" not in source


def test_onion_page_section_handles_initial_load_error():
    class FakePreferences:
        def load(self):
            raise ValueError("Invalid Onion configuration")

    section = OnionPageSection.__new__(OnionPageSection)
    section.preferences = FakePreferences()

    result = section._try_load_initial_selection()

    assert result is None
    assert section._preferences_load_failed is True
    assert section._preferences_load_error == (
        "Invalid Onion configuration"
    )


def test_onion_page_section_clears_error_after_successful_load():
    class FakePreferences:
        def load(self):
            return True, "/tmp/onion.html"

    section = OnionPageSection.__new__(OnionPageSection)
    section.preferences = FakePreferences()
    section._preferences_load_error = "Previous error"

    result = section._try_load_initial_selection()

    assert result == (True, "/tmp/onion.html")
    assert section._preferences_load_failed is False
    assert section._preferences_load_error is None


def test_onion_page_section_constructor_uses_safe_loader():
    import inspect

    source = inspect.getsource(OnionPageSection.__init__)

    assert "self._try_load_initial_selection()" in source
    assert "self._load_initial_selection()" not in source


def test_onion_page_section_constructor_handles_missing_selection():
    import inspect

    source = inspect.getsource(OnionPageSection.__init__)

    assert "if selection is None:" in source
    assert "enabled, html_path = selection" in source


def test_onion_page_section_disables_save_after_load_failure():
    class FakeButton:
        def __init__(self):
            self.states = []

        def state(self, values):
            self.states.append(tuple(values))

    section = OnionPageSection.__new__(OnionPageSection)
    section._preferences_load_failed = True
    section.save_button = FakeButton()

    section._update_save_button_state()

    assert section.save_button.states == [("disabled",)]


def test_onion_page_section_enables_save_after_successful_load():
    class FakeButton:
        def __init__(self):
            self.states = []

        def state(self, values):
            self.states.append(tuple(values))

    section = OnionPageSection.__new__(OnionPageSection)
    section._preferences_load_failed = False
    section.save_button = FakeButton()

    section._update_save_button_state()

    assert section.save_button.states == [("!disabled",)]


def test_onion_page_section_constructor_updates_save_button_state():
    import inspect

    source = inspect.getsource(OnionPageSection.__init__)

    assert "self._update_save_button_state()" in source


def test_onion_page_section_constructor_updates_state_after_button_creation():
    import inspect

    source = inspect.getsource(OnionPageSection.__init__)

    button_position = source.index("self.save_button =")
    update_position = source.index("self._update_save_button_state()")

    assert update_position > button_position


def test_onion_page_section_updates_actual_save_button():
    class FakeButton:
        def __init__(self):
            self.states = []

        def state(self, values):
            self.states.append(tuple(values))

    section = OnionPageSection.__new__(OnionPageSection)
    section._preferences_load_failed = True
    section.save_button = FakeButton()

    section._update_save_button_state()

    assert section.save_button.states == [("disabled",)]


def test_onion_page_section_formats_load_error_message():
    section = OnionPageSection.__new__(OnionPageSection)
    section._preferences_load_error = "Invalid Onion configuration"

    message = section._load_error_message()

    assert "Invalid Onion configuration" in message
    assert "salvataggio" in message.lower()


def test_onion_page_section_has_no_message_after_successful_load():
    section = OnionPageSection.__new__(OnionPageSection)
    section._preferences_load_error = None

    assert section._load_error_message() == ""


def test_onion_page_section_creates_error_label_after_failed_load(
    monkeypatch,
):
    import garlicsmtp.gui.tk_onion_page_section as module

    calls = []

    class FakeLabel:
        def __init__(self, parent, **kwargs):
            calls.append(("create", parent, kwargs))

        def grid(self, **kwargs):
            calls.append(("grid", kwargs))

    monkeypatch.setattr(module.ttk, "Label", FakeLabel)

    section = OnionPageSection.__new__(OnionPageSection)
    section._preferences_load_error = "Invalid Onion configuration"

    section._create_load_error_label()

    assert len(calls) == 2
    assert calls[0][0] == "create"
    assert "Invalid Onion configuration" in calls[0][2]["text"]
    assert calls[1][0] == "grid"
    assert calls[1][1]["row"] == 3


def test_onion_page_section_does_not_create_error_label_after_success(
    monkeypatch,
):
    import garlicsmtp.gui.tk_onion_page_section as module

    calls = []

    def fake_label(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("Error label must not be created")

    monkeypatch.setattr(module.ttk, "Label", fake_label)

    section = OnionPageSection.__new__(OnionPageSection)
    section._preferences_load_error = None

    section._create_load_error_label()

    assert calls == []


def test_onion_page_section_constructor_creates_load_error_label():
    import inspect

    source = inspect.getsource(OnionPageSection.__init__)

    assert "self._create_load_error_label()" in source


def test_onion_page_section_constructor_creates_error_label_after_save_button():
    import inspect

    source = inspect.getsource(OnionPageSection.__init__)

    button_position = source.index("self.save_button =")
    error_position = source.index("self._create_load_error_label()")

    assert error_position > button_position


def test_onion_page_section_save_callback_uses_selected_checkbox(
    monkeypatch,
):
    import garlicsmtp.gui.tk_onion_page_section as module

    calls = []

    class FakeVar:
        def __init__(self, value):
            self.value = value

        def get(self):
            return self.value

    class FakePreferences:
        def save(self, *, enabled, html_path):
            calls.append((enabled, html_path))

    section = OnionPageSection.__new__(OnionPageSection)
    section.preferences = FakePreferences()
    section._preferences_load_failed = False
    section.enabled_var = FakeVar(True)
    section.html_path_var = FakeVar("/tmp/personal.html")

    monkeypatch.setattr(
        module.messagebox,
        "showinfo",
        lambda *args, **kwargs: None,
    )

    section._on_save()

    assert calls == [(True, "/tmp/personal.html")]