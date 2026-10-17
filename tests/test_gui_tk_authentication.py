# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import tkinter as tk
from tkinter import ttk

from garlicsmtp.gui.tk_authentication import (
    LoginDialog,
    LoginForm,
    SetupDialog,
    SetupForm,
    prompt_login,
    prompt_setup,
    RecoveryDialog,
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


def test_login_form_uses_orange_background_and_black_text():
    root = tk.Tk()
    root.withdraw()

    try:
        form = LoginForm(
            root,
        )

        style = ttk.Style(root)

        assert form.cget("style") == "Garlic.Auth.TFrame"

        assert (
            style.lookup(
                "Garlic.Auth.TFrame",
                "background",
            )
            == "#ff8c00"
        )
        assert (
            style.lookup(
                "Garlic.Auth.TLabel",
                "background",
            )
            == "#ff8c00"
        )
        assert (
            style.lookup(
                "Garlic.Auth.TLabel",
                "foreground",
            )
            == "#000000"
        )

        assert (
            form.username_entry.cget("style")
            == ""
        )
        assert (
            form.password_entry.cget("style")
            == ""
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


def test_login_dialog_is_centered_on_screen():
    root = tk.Tk()
    root.withdraw()

    try:
        dialog = LoginDialog(
            root,
        )

        dialog.update_idletasks()

        expected_x = (
            dialog.winfo_screenwidth()
            - dialog.winfo_width()
        ) // 2
        expected_y = (
            dialog.winfo_screenheight()
            - dialog.winfo_height()
        ) // 2

        assert dialog.geometry().endswith(
            f"+{expected_x}+{expected_y}"
        )

    finally:
        dialog.destroy()
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


def test_recovery_dialog_cancel_keeps_result_false():
    root = tk.Tk()
    root.withdraw()

    try:
        dialog = RecoveryDialog(
            root,
            "test-recovery-key",
        )

        assert dialog.result is False

        dialog.cancel()

        assert dialog.result is False
        assert not dialog.winfo_exists()

    finally:
        root.destroy()


def test_recovery_dialog_accept_confirms_recovery():
    root = tk.Tk()
    root.withdraw()

    try:
        dialog = RecoveryDialog(
            root,
            "test-recovery-key",
        )

        assert dialog.result is False

        dialog.reentry_entry.insert(0, "test-recovery-key")
        dialog.accept()

        assert dialog.result == 'test-recovery-key'
        assert not dialog.winfo_exists()

    finally:
        root.destroy()


def test_recovery_dialog_displays_recovery_key():
    root = tk.Tk()
    root.withdraw()

    try:
        recovery_key = "a1b2c3d4" * 8

        dialog = RecoveryDialog(
            root,
            recovery_key,
        )

        assert dialog.recovery_key_entry.get() == recovery_key

        assert (
            dialog.recovery_key_entry.winfo_manager()
            == "grid"
        )

        assert (
            str(dialog.recovery_key_entry.cget("state"))
            == "readonly"
        )

    finally:
        root.destroy()


def test_recovery_dialog_confirm_button_accepts():
    root = tk.Tk()
    root.withdraw()

    try:
        dialog = RecoveryDialog(
            root,
            "a1b2c3d4" * 8,
        )

        assert dialog.result is False

        assert (
            dialog.confirm_button.winfo_manager()
            == "grid"
        )

        dialog.reentry_entry.insert(0, "a1b2c3d4" * 8)
        dialog.confirm_button.invoke()

        assert dialog.result == 'a1b2c3d4a1b2c3d4a1b2c3d4a1b2c3d4a1b2c3d4a1b2c3d4a1b2c3d4a1b2c3d4'
        assert not dialog.winfo_exists()

    finally:
        root.destroy()


def test_recovery_dialog_window_close_cancels():
    root = tk.Tk()
    root.withdraw()

    try:
        dialog = RecoveryDialog(
            root,
            "a1b2c3d4" * 8,
        )

        close_command = dialog.protocol(
            "WM_DELETE_WINDOW"
        )

        assert close_command

        dialog.tk.call(
            close_command,
        )

        assert dialog.result is False
        assert not dialog.winfo_exists()

    finally:
        root.destroy()


def test_recovery_dialog_displays_security_warning():
    root = tk.Tk()
    root.withdraw()

    try:
        dialog = RecoveryDialog(
            root,
            "a1b2c3d4" * 8,
        )

        warning = dialog.warning_label.cget("text")

        assert "save" in warning.lower()
        assert "recovery key" in warning.lower()
        assert "lose" in warning.lower()

        assert (
            dialog.warning_label.winfo_manager()
            == "grid"
        )

    finally:
        root.destroy()

def test_recovery_dialog_key_is_selectable_and_readonly():
    root = tk.Tk()
    root.withdraw()

    try:
        recovery_key = "a1b2c3d4" * 8

        dialog = RecoveryDialog(
            root,
            recovery_key,
        )

        entry = dialog.recovery_key_entry

        assert isinstance(entry, ttk.Entry)
        assert entry.get() == recovery_key
        assert str(entry.cget("state")) == "readonly"
        assert entry.winfo_manager() == "grid"

    finally:
        root.destroy()


def test_recovery_dialog_copy_button_copies_key():
    root = tk.Tk()
    root.withdraw()

    try:
        recovery_key = "a1b2c3d4" * 8

        dialog = RecoveryDialog(
            root,
            recovery_key,
        )

        # Intercettiamo gli appunti per non usare
        # quelli reali durante il test.
        copied = []

        dialog.clipboard_clear = lambda: copied.append("clear")
        dialog.clipboard_append = lambda text: copied.append(text)

        assert dialog.copy_button.winfo_manager() == "grid"

        dialog.copy_button.invoke()

        assert copied == ["clear", recovery_key]
        assert dialog.winfo_exists()

    finally:
        root.destroy()


def test_recovery_dialog_copy_button_copies_key():
    root = tk.Tk()
    root.withdraw()

    try:
        recovery_key = "a1b2c3d4" * 8

        dialog = RecoveryDialog(
            root,
            recovery_key,
        )

        # Intercettiamo gli appunti per non usare
        # quelli reali durante il test.
        copied = []

        dialog.clipboard_clear = lambda: copied.append("clear")
        dialog.clipboard_append = lambda text: copied.append(text)

        assert dialog.copy_button.winfo_manager() == "grid"

        dialog.copy_button.invoke()

        assert copied == ["clear", recovery_key]
        assert dialog.winfo_exists()

    finally:
        root.destroy()


def test_recovery_dialog_cannot_confirm_without_reentering_key():
    root = tk.Tk()
    root.withdraw()

    try:
        dialog = RecoveryDialog(
            root,
            "a1b2c3d4" * 8,
        )

        dialog.confirm_button.invoke()

        assert dialog.result is False
        assert dialog.winfo_exists()

    finally:
        root.destroy()


def test_login_form_forgot_password_invokes_callback():
    root = tk.Tk()
    root.withdraw()

    try:
        recovery_requests = []
        submitted = []

        form = LoginForm(
            root,
            on_submit=submitted.append,
            on_forgot_password=lambda: recovery_requests.append(True),
        )

        assert form.forgot_password_button.cget("text") == (
            "Forgotten password?"
        )

        form.forgot_password_button.invoke()

        assert recovery_requests == [True]
        assert submitted == []

    finally:
        root.destroy()


def test_login_dialog_forgot_password_returns_recovery_request():
    root = tk.Tk()
    root.withdraw()

    try:
        dialog = LoginDialog(root)

        dialog.form.forgot_password_button.invoke()

        assert dialog.result == "forgot_password"
        assert not dialog.winfo_exists()

    finally:
        root.destroy()


def test_password_reset_dialog_collects_credentials_and_masks_secrets():
    from garlicsmtp.gui.tk_authentication import PasswordResetDialog

    root = tk.Tk()
    root.withdraw()

    try:
        dialog = PasswordResetDialog(root)

        assert dialog.recovery_key_entry.cget("show") == "*"
        assert dialog.new_password_entry.cget("show") == "*"
        assert dialog.password_confirmation_entry.cget("show") == "*"

        dialog.username_entry.insert(0, "alice")
        dialog.recovery_key_entry.insert(0, "old-recovery-key")
        dialog.new_password_entry.insert(0, "NewPassword123!")
        dialog.password_confirmation_entry.insert(0, "NewPassword123!")

        dialog.reset_button.invoke()

        assert dialog.result == (
            "alice",
            "old-recovery-key",
            "NewPassword123!",
        )
        assert not dialog.winfo_exists()
    finally:
        root.destroy()


def test_password_reset_dialog_rejects_mismatched_passwords():
    from garlicsmtp.gui.tk_authentication import PasswordResetDialog

    root = tk.Tk()
    root.withdraw()

    try:
        dialog = PasswordResetDialog(root)

        dialog.username_entry.insert(0, "alice")
        dialog.recovery_key_entry.insert(0, "old-recovery-key")
        dialog.new_password_entry.insert(0, "NewPassword123!")
        dialog.password_confirmation_entry.insert(0, "DifferentPassword123!")

        dialog.reset_button.invoke()

        assert dialog.result is None
        assert dialog.winfo_exists()
    finally:
        root.destroy()


def test_password_reset_dialog_cancel_does_not_submit_credentials():
    from garlicsmtp.gui.tk_authentication import PasswordResetDialog

    root = tk.Tk()
    root.withdraw()

    try:
        dialog = PasswordResetDialog(root)

        dialog.username_entry.insert(0, "alice")
        dialog.recovery_key_entry.insert(0, "old-recovery-key")
        dialog.new_password_entry.insert(0, "NewPassword123!")

        dialog.cancel()

        assert dialog.result is None
        assert not dialog.winfo_exists()
    finally:
        root.destroy()
