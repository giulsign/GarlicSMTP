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
    assert "saving disabled" in message.lower()


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
        def save_combined(
            self,
            *,
            custom_enabled,
            custom_html_path,
            website_enabled,
            website_index_path,
        ):
            calls.append(
                (
                    custom_enabled,
                    custom_html_path,
                    website_enabled,
                    website_index_path,
                )
            )


    section = OnionPageSection.__new__(OnionPageSection)
    section.preferences = FakePreferences()
    section._preferences_load_failed = False
    section.enabled_var = FakeVar(True)
    section.html_path_var = FakeVar("/tmp/personal.html")
    section.website_enabled_var = FakeVar(False)
    section.website_html_path_var = FakeVar("")

    monkeypatch.setattr(
        module.messagebox,
        "showinfo",
        lambda *args, **kwargs: None,
    )

    section._on_save()

    
    assert calls == [
        (
            True,
            "/tmp/personal.html",
            False,
            "",
        )
    ]



def test_onion_page_section_uses_english_interface_text():
    import inspect

    source = inspect.getsource(OnionPageSection)

    expected_texts = (
        "Personal Onion Page",
        "Enable custom presence HTML page",
        "HTML file path:",
        "Save preferences",
        "Onion configuration error",
        "Preferences saved",
        "Unable to load Onion configuration:",
        "Saving disabled.",
    )

    for text in expected_texts:
        assert text in source



def test_onion_page_section_loads_website_preferences():
    class FakePreferences:
        def load_website(self):
            return True, "website/index.html"

    section = OnionPageSection.__new__(OnionPageSection)
    section.preferences = FakePreferences()

    assert section.load_website_selection() == (
        True,
        "website/index.html",
    )



def test_onion_page_section_marks_failed_website_initial_load():
    class FakePreferences:
        def load_website(self):
            raise ValueError("Invalid website configuration")

    section = OnionPageSection.__new__(OnionPageSection)
    section.preferences = FakePreferences()
    section._preferences_load_failed = False

    with pytest.raises(
        ValueError,
        match="Invalid website configuration",
    ):
        section._load_initial_website_selection()

    assert section._preferences_load_failed is True



def test_onion_page_section_handles_initial_website_load_error():
    class FakePreferences:
        def load_website(self):
            raise ValueError("Invalid website configuration")

    section = OnionPageSection.__new__(OnionPageSection)
    section.preferences = FakePreferences()

    result = section._try_load_initial_website_selection()

    assert result is None
    assert section._preferences_load_failed is True
    assert section._preferences_load_error == (
        "Invalid website configuration"
    )



def test_onion_page_section_constructor_loads_website_preferences():
    import inspect

    source = inspect.getsource(OnionPageSection.__init__)

    assert "self._try_load_initial_website_selection()" in source



def test_onion_page_section_constructor_creates_website_checkbox():
    import inspect

    source = inspect.getsource(OnionPageSection.__init__)

    assert "Enable Onion website" in source
    assert "variable=self.website_enabled_var" in source



def test_onion_page_section_constructor_creates_website_path_entry():
    import inspect

    source = inspect.getsource(OnionPageSection.__init__)

    assert "Website HTML file:" in source
    assert "textvariable=self.website_html_path_var" in source



def test_onion_page_section_browse_website_html(
    monkeypatch,
):
    class FakeStringVar:
        def __init__(self):
            self.value = ""

        def set(self, value):
            self.value = value

    selected = FakeStringVar()

    section = OnionPageSection.__new__(OnionPageSection)
    section.website_html_path_var = selected

    def fake_askopenfilename(**kwargs):
        return "/home/user/website/index.html"

    monkeypatch.setattr(
        "garlicsmtp.gui.tk_onion_page_section.filedialog.askopenfilename",
        fake_askopenfilename,
    )

    section._browse_website_html()

    assert selected.value == "/home/user/website/index.html"



def test_onion_page_section_constructor_creates_website_browse_button():
    import inspect

    source = inspect.getsource(OnionPageSection.__init__)

    assert 'text="Browse..."' in source
    assert "command=self._browse_website_html" in source



def test_onion_page_section_saves_website_selection():
    calls = []

    class FakePreferences:
        def save_website(self, *, enabled, html_path):
            calls.append((enabled, html_path))

    section = OnionPageSection.__new__(OnionPageSection)
    section.preferences = FakePreferences()

    section.save_website_selection(
        enabled=True,
        html_path="website/index.html",
    )

    assert calls == [
        (True, "website/index.html"),
    ]



def test_onion_page_section_on_save_includes_website(
    monkeypatch,
    tmp_path,
):
    website_index = tmp_path / "index.html"
    website_index.write_text(
        "<html><body>Test</body></html>",
        encoding="utf-8",
    )
    calls = []

    class FakeVar:
        def __init__(self, value):
            self.value = value

        def get(self):
            return self.value

    section = OnionPageSection.__new__(OnionPageSection)
    section._preferences_load_failed = False

    section.enabled_var = FakeVar(False)
    section.html_path_var = FakeVar("")
    section.website_enabled_var = FakeVar(True)
    section.website_html_path_var = FakeVar(
        str(website_index)
    )
    
    section.save_combined_selection = lambda **kwargs: calls.append(
        kwargs
    )

    monkeypatch.setattr(
        "garlicsmtp.gui.tk_onion_page_section.messagebox.showinfo",
        lambda *args, **kwargs: None,
    )

    section._on_save()

    assert calls == [
        {
            "custom_enabled": False,
            "custom_html_path": "",
            "website_enabled": True,
            "website_index_path": str(website_index),
        }
    ]



def test_onion_page_section_does_not_save_custom_if_website_invalid(
    monkeypatch,
):
    import garlicsmtp.gui.tk_onion_page_section as module

    calls = []
    errors = []

    class FakeVar:
        def __init__(self, value):
            self.value = value

        def get(self):
            return self.value

    section = OnionPageSection.__new__(OnionPageSection)
    section.enabled_var = FakeVar(True)
    section.html_path_var = FakeVar("/tmp/personal.html")
    section.website_enabled_var = FakeVar(True)
    section.website_html_path_var = FakeVar("")

    def save_custom(*, enabled, html_path):
        calls.append("custom")

    def save_website(*, enabled, html_path):
        if enabled and not html_path.strip():
            raise ValueError("Website HTML path is required")
        calls.append("website")

    section.save_selection = save_custom
    section.save_website_selection = save_website

    monkeypatch.setattr(
        module.messagebox,
        "showerror",
        lambda *args, **kwargs: errors.append(args),
    )

    section._on_save()

    assert calls == []
    assert len(errors) == 1



def test_onion_page_section_does_not_save_custom_if_website_file_missing(
    monkeypatch,
    tmp_path,
):
    import garlicsmtp.gui.tk_onion_page_section as module

    calls = []
    errors = []
    missing_path = tmp_path / "missing" / "index.html"

    class FakeVar:
        def __init__(self, value):
            self.value = value

        def get(self):
            return self.value

    section = OnionPageSection.__new__(OnionPageSection)
    section.enabled_var = FakeVar(True)
    section.html_path_var = FakeVar("/tmp/personal.html")
    section.website_enabled_var = FakeVar(True)
    section.website_html_path_var = FakeVar(str(missing_path))

    def save_custom(*, enabled, html_path):
        calls.append("custom")

    def save_website(*, enabled, html_path):
        if enabled and not missing_path.is_file():
            raise ValueError("Website HTML file does not exist")
        calls.append("website")

    section.save_selection = save_custom
    section.save_website_selection = save_website

    monkeypatch.setattr(
        module.messagebox,
        "showerror",
        lambda *args, **kwargs: errors.append(args),
    )

    section._on_save()

    assert calls == []
    assert len(errors) == 1



def test_save_onion_combined_settings_updates_both_modes(
    tmp_path,
):
    import tomllib

    from garlicsmtp.configuration.onion_page_writer import (
        save_onion_combined_settings,
    )

    config_path = tmp_path / "config.toml"
    config_path.write_text(
        '[tor]\n'
        'onion_custom_page_enabled = false\n'
        'onion_custom_page_path = ""\n'
        'onion_website_enabled = false\n'
        'onion_website_index_path = ""\n'
        '\n'
        '[smtp]\n'
        'port = 2525\n',
        encoding="utf-8",
    )

    save_onion_combined_settings(
        config_path,
        custom_enabled=True,
        custom_html_path="custom.html",
        website_enabled=True,
        website_index_path="website/index.html",
    )

    parsed = tomllib.loads(
        config_path.read_text(encoding="utf-8")
    )

    assert parsed["tor"]["onion_custom_page_enabled"] is True
    assert parsed["tor"]["onion_custom_page_path"] == "custom.html"
    assert parsed["tor"]["onion_website_enabled"] is True
    assert (
        parsed["tor"]["onion_website_index_path"]
        == "website/index.html"
    )
    assert parsed["smtp"]["port"] == 2525



def test_onion_page_section_saves_combined_selection():
    calls = []

    class FakePreferences:
        def save_combined(self, **kwargs):
            calls.append(kwargs)

    section = OnionPageSection.__new__(OnionPageSection)
    section.preferences = FakePreferences()
    section._preferences_load_failed = False

    section.save_combined_selection(
        custom_enabled=True,
        custom_html_path="custom.html",
        website_enabled=True,
        website_index_path="website/index.html",
    )

    assert calls == [
        {
            "custom_enabled": True,
            "custom_html_path": "custom.html",
            "website_enabled": True,
            "website_index_path": "website/index.html",
        }
    ]



def test_onion_page_section_on_save_uses_combined_selection(
    tmp_path,
    monkeypatch,
):
    import pytest
    import garlicsmtp.gui.tk_onion_page_section as module

    class FakeVar:
        def __init__(self, value):
            self.value = value

        def get(self):
            return self.value

    website_index = tmp_path / "index.html"
    website_index.write_text("<html></html>", encoding="utf-8")

    section = module.OnionPageSection.__new__(
        module.OnionPageSection
    )

    section.enabled_var = FakeVar(True)
    section.html_path_var = FakeVar("custom.html")
    section.website_enabled_var = FakeVar(True)
    section.website_html_path_var = FakeVar(
        str(website_index)
    )

    combined_calls = []
    separate_calls = []
    success_messages = []
    error_messages = []

    section.save_combined_selection = lambda **kwargs: (
        combined_calls.append(kwargs)
    )
    section.save_selection = lambda **kwargs: (
        separate_calls.append(("custom", kwargs))
    )
    section.save_website_selection = lambda **kwargs: (
        separate_calls.append(("website", kwargs))
    )

    monkeypatch.setattr(
        module.messagebox,
        "showinfo",
        lambda *args, **kwargs: success_messages.append(args),
    )
    monkeypatch.setattr(
        module.messagebox,
        "showerror",
        lambda *args, **kwargs: error_messages.append(args),
    )

    section._on_save()

    assert combined_calls == [
        {
            "custom_enabled": True,
            "custom_html_path": "custom.html",
            "website_enabled": True,
            "website_index_path": str(website_index),
        }
    ]
    assert separate_calls == []
    assert len(success_messages) == 1
    assert error_messages == []



def test_onion_page_section_on_save_handles_failed_load(
    monkeypatch,
):
    import garlicsmtp.gui.tk_onion_page_section as module

    class FakeVar:
        def __init__(self, value):
            self.value = value

        def get(self):
            return self.value

    section = OnionPageSection.__new__(OnionPageSection)
    section._preferences_load_failed = True

    section.enabled_var = FakeVar(False)
    section.html_path_var = FakeVar("")
    section.website_enabled_var = FakeVar(False)
    section.website_html_path_var = FakeVar("")

    calls = []
    errors = []
    successes = []

    class FakePreferences:
        def save_combined(self, **kwargs):
            calls.append(kwargs)

    section.preferences = FakePreferences()

    monkeypatch.setattr(
        module.messagebox,
        "showerror",
        lambda *args, **kwargs: errors.append(args),
    )
    monkeypatch.setattr(
        module.messagebox,
        "showinfo",
        lambda *args, **kwargs: successes.append(args),
    )

    section._on_save()

    assert calls == []
    assert len(errors) == 1
    assert errors[0][0] == "Onion configuration error"
    assert successes == []



def test_onion_page_section_on_save_accepts_website_path_relative_to_config(
    tmp_path,
    monkeypatch,
):
    import garlicsmtp.gui.tk_onion_page_section as module

    class FakeVar:
        def __init__(self, value):
            self.value = value

        def get(self):
            return self.value

    config_dir = tmp_path / "config"
    config_dir.mkdir()

    website_dir = config_dir / "website"
    website_dir.mkdir()

    (website_dir / "index.html").write_text(
        "<html><body>Test</body></html>",
        encoding="utf-8",
    )

    settings_path = config_dir / "settings.toml"

    class FakePreferences:
        def __init__(self):
            self.settings_path = settings_path

    section = OnionPageSection.__new__(OnionPageSection)
    section.preferences = FakePreferences()
    section._preferences_load_failed = False

    section.enabled_var = FakeVar(False)
    section.html_path_var = FakeVar("")
    section.website_enabled_var = FakeVar(True)
    section.website_html_path_var = FakeVar("website/index.html")

    calls = []
    errors = []
    successes = []

    section.save_combined_selection = lambda **kwargs: calls.append(
        kwargs
    )

    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr(
        module.messagebox,
        "showerror",
        lambda *args, **kwargs: errors.append(args),
    )
    monkeypatch.setattr(
        module.messagebox,
        "showinfo",
        lambda *args, **kwargs: successes.append(args),
    )

    section._on_save()

    assert calls == [
        {
            "custom_enabled": False,
            "custom_html_path": "",
            "website_enabled": True,
            "website_index_path": "website/index.html",
        }
    ]
    assert errors == []
    assert len(successes) == 1
