# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import tkinter as tk

from garlicsmtp.gui.tk_authentication import (
    LoginDialog,
    LoginForm,
    SetupDialog,
    SetupForm,
    prompt_login,
    prompt_setup,
)


def test_login_form_collects_username_and_password():
    root = tk.Tk()
    root.withdraw()

    try:
        form = LoginForm(
            root,
        )

        form.username_entry.insert(
            0,
            "alice",
        )
        form.password_entry.insert(
            0,
            "Garlic1!",
        )

        assert form.credentials() == (
            "alice",
            "Garlic1!",
        )

    finally:
        root.destroy()


def test_login_form_masks_password():
    root = tk.Tk()
    root.withdraw()

    try:
        form = LoginForm(
            root,
        )

        assert (
            form.password_entry.cget("show")
            == "*"
        )

    finally:
        root.destroy()


def test_setup_form_collects_username_password_and_confirmation():
    root = tk.Tk()
    root.withdraw()

    try:
        form = SetupForm(
            root,
        )

        form.username_entry.insert(
            0,
            "alice",
        )
        form.password_entry.insert(
            0,
            "Garlic1!",
        )
        form.password_confirmation_entry.insert(
            0,
            "Garlic1!",
        )

        assert form.credentials() == (
            "alice",
            "Garlic1!",
            "Garlic1!",
        )

    finally:
        root.destroy()


def test_setup_form_masks_password_and_confirmation():
    root = tk.Tk()
    root.withdraw()

    try:
        form = SetupForm(
            root,
        )

        assert (
            form.password_entry.cget("show")
            == "*"
        )
        assert (
            form.password_confirmation_entry.cget("show")
            == "*"
        )

    finally:
        root.destroy()


def test_login_form_submits_credentials():
    root = tk.Tk()
    root.withdraw()

    try:
        submitted = []

        form = LoginForm(
            root,
            on_submit=submitted.append,
        )

        form.username_entry.insert(
            0,
            "alice",
        )
        form.password_entry.insert(
            0,
            "Garlic1!",
        )

        form.login_button.invoke()

        assert submitted == [
            (
                "alice",
                "Garlic1!",
            )
        ]

    finally:
        root.destroy()


def test_setup_form_submits_credentials():
    root = tk.Tk()
    root.withdraw()

    try:
        submitted = []

        form = SetupForm(
            root,
            on_submit=submitted.append,
        )

        form.username_entry.insert(
            0,
            "alice",
        )
        form.password_entry.insert(
            0,
            "Garlic1!",
        )
        form.password_confirmation_entry.insert(
            0,
            "Garlic1!",
        )

        form.create_button.invoke()

        assert submitted == [
            (
                "alice",
                "Garlic1!",
                "Garlic1!",
            )
        ]

    finally:
        root.destroy()


def test_login_dialog_accepts_credentials():
    root = tk.Tk()
    root.withdraw()

    try:
        dialog = LoginDialog(
            root,
        )

        dialog.form.username_entry.insert(
            0,
            "alice",
        )
        dialog.form.password_entry.insert(
            0,
            "Garlic1!",
        )

        dialog.form.login_button.invoke()

        assert dialog.result == (
            "alice",
            "Garlic1!",
        )
        assert not dialog.winfo_exists()

    finally:
        root.destroy()


def test_login_dialog_cancel_keeps_result_none():
    root = tk.Tk()
    root.withdraw()

    try:
        dialog = LoginDialog(
            root,
        )

        dialog.cancel()

        assert dialog.result is None
        assert not dialog.winfo_exists()

    finally:
        root.destroy()


def test_login_dialog_window_close_cancels():
    root = tk.Tk()
    root.withdraw()

    try:
        dialog = LoginDialog(
            root,
        )

        close_command = dialog.protocol(
            "WM_DELETE_WINDOW"
        )

        assert close_command

        dialog.tk.call(
            close_command,
        )

        assert dialog.result is None
        assert not dialog.winfo_exists()

    finally:
        root.destroy()


def test_setup_dialog_accepts_credentials():
    root = tk.Tk()
    root.withdraw()

    try:
        dialog = SetupDialog(
            root,
        )

        dialog.form.username_entry.insert(
            0,
            "alice",
        )
        dialog.form.password_entry.insert(
            0,
            "Garlic1!",
        )
        dialog.form.password_confirmation_entry.insert(
            0,
            "Garlic1!",
        )

        dialog.form.create_button.invoke()

        assert dialog.result == (
            "alice",
            "Garlic1!",
            "Garlic1!",
        )
        assert not dialog.winfo_exists()

    finally:
        root.destroy()


def test_setup_dialog_cancel_keeps_result_none():
    root = tk.Tk()
    root.withdraw()

    try:
        dialog = SetupDialog(
            root,
        )

        dialog.cancel()

        assert dialog.result is None
        assert not dialog.winfo_exists()

    finally:
        root.destroy()


def test_prompt_login_waits_for_dialog_and_returns_result(
    monkeypatch,
):
    events = []

    class FakeDialog:

        def __init__(
            self,
            master,
        ) -> None:
            events.append(
                ("create", master)
            )
            self.result = (
                "alice",
                "Garlic1!",
            )

        def grab_set(
            self,
        ) -> None:
            events.append(
                ("grab",)
            )

        def wait_window(
            self,
        ) -> None:
            events.append(
                ("wait",)
            )

    master = object()

    monkeypatch.setattr(
        "garlicsmtp.gui.tk_authentication.LoginDialog",
        FakeDialog,
    )

    result = prompt_login(
        master,
    )

    assert result == (
        "alice",
        "Garlic1!",
    )
    assert events == [
        ("create", master),
        ("grab",),
        ("wait",),
    ]


def test_prompt_setup_waits_for_dialog_and_returns_result(
    monkeypatch,
):
    events = []

    class FakeDialog:

        def __init__(
            self,
            master,
        ) -> None:
            events.append(
                ("create", master)
            )
            self.result = (
                "alice",
                "Garlic1!",
                "Garlic1!",
            )

        def grab_set(
            self,
        ) -> None:
            events.append(
                ("grab",)
            )

        def wait_window(
            self,
        ) -> None:
            events.append(
                ("wait",)
            )

    master = object()

    monkeypatch.setattr(
        "garlicsmtp.gui.tk_authentication.SetupDialog",
        FakeDialog,
    )

    result = prompt_setup(
        master,
    )

    assert result == (
        "alice",
        "Garlic1!",
        "Garlic1!",
    )
    assert events == [
        ("create", master),
        ("grab",),
        ("wait",),
    ]


def test_login_form_lays_out_controls():
    root = tk.Tk()
    root.withdraw()

    try:
        form = LoginForm(
            root,
        )

        assert (
            form.username_entry.winfo_manager()
            == "grid"
        )
        assert (
            form.password_entry.winfo_manager()
            == "grid"
        )
        assert (
            form.login_button.winfo_manager()
            == "grid"
        )

    finally:
        root.destroy()


def test_setup_form_lays_out_controls():
    root = tk.Tk()
    root.withdraw()

    try:
        form = SetupForm(
            root,
        )

        assert (
            form.username_entry.winfo_manager()
            == "grid"
        )
        assert (
            form.password_entry.winfo_manager()
            == "grid"
        )
        assert (
            form.password_confirmation_entry.winfo_manager()
            == "grid"
        )
        assert (
            form.create_button.winfo_manager()
            == "grid"
        )

    finally:
        root.destroy()


def test_login_dialog_lays_out_form():
    root = tk.Tk()
    root.withdraw()

    try:
        dialog = LoginDialog(
            root,
        )

        assert (
            dialog.form.winfo_manager()
            == "grid"
        )

    finally:
        dialog.destroy()
        root.destroy()


def test_setup_dialog_lays_out_form():
    root = tk.Tk()
    root.withdraw()

    try:
        dialog = SetupDialog(
            root,
        )

        assert (
            dialog.form.winfo_manager()
            == "grid"
        )

    finally:
        dialog.destroy()
        root.destroy()


def test_prompt_login_grabs_dialog_before_waiting(
    monkeypatch,
):
    events = []

    class FakeDialog:

        def __init__(
            self,
            master,
        ) -> None:
            events.append(
                ("create", master)
            )
            self.result = None

        def grab_set(
            self,
        ) -> None:
            events.append(
                ("grab",)
            )

        def wait_window(
            self,
        ) -> None:
            events.append(
                ("wait",)
            )

    master = object()

    monkeypatch.setattr(
        "garlicsmtp.gui.tk_authentication.LoginDialog",
        FakeDialog,
    )

    prompt_login(
        master,
    )

    assert events == [
        ("create", master),
        ("grab",),
        ("wait",),
    ]


def test_prompt_setup_grabs_dialog_before_waiting(
    monkeypatch,
):
    events = []

    class FakeDialog:

        def __init__(
            self,
            master,
        ) -> None:
            events.append(
                ("create", master)
            )
            self.result = None

        def grab_set(
            self,
        ) -> None:
            events.append(
                ("grab",)
            )

        def wait_window(
            self,
        ) -> None:
            events.append(
                ("wait",)
            )

    master = object()

    monkeypatch.setattr(
        "garlicsmtp.gui.tk_authentication.SetupDialog",
        FakeDialog,
    )

    prompt_setup(
        master,
    )

    assert events == [
        ("create", master),
        ("grab",),
        ("wait",),
    ]