# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import tkinter as tk
from tkinter import ttk


class LoginForm(ttk.Frame):

    def __init__(
        self,
        master,
        *,
        on_submit=None,
        on_forgot_password=None,
    ) -> None:
        super().__init__(
            master,
            style="Garlic.Auth.TFrame",
        )

        style = ttk.Style(self)
        style.configure(
            "Garlic.Auth.TFrame",
            background="#ff8c00",
        )
        style.configure(
            "Garlic.Auth.TLabel",
            background="#ff8c00",
            foreground="#000000",
        ) 
        
        self.on_submit = on_submit
        self.on_forgot_password = on_forgot_password

        ttk.Label(
            self,
            text="Username",
            style="Garlic.Auth.TLabel",
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, 12),
            pady=3,
        )

        ttk.Label(
            self,
            text="Password",
            style="Garlic.Auth.TLabel",
        ).grid(
            row=1,
            column=0,
            sticky="w",
            padx=(0, 12),
            pady=3,
        )

        self.username_entry = ttk.Entry(
            self,
        )

        self.username_entry.grid(
            row=0,
            column=1,
            sticky="ew",
            pady=3,
        )

        self.password_entry = ttk.Entry(
            self,
            show="*",
        )

        self.password_entry.grid(
            row=1,
            column=1,
            sticky="ew",
            pady=3,
        )

        self.login_button = ttk.Button(
            self,
            text="Login",
            command=self.submit,
        )

        self.login_button.grid(
            row=2,
            column=1,
            sticky="e",
            pady=(8, 0),
        )


        self.forgot_password_button = ttk.Button(
            self,
            text="Forgotten password?",
            command=self.forgot_password,
        )
        self.forgot_password_button.grid(
            row=3,
            column=1,
            sticky="e",
            pady=(6, 0),
        )

        self.columnconfigure(
            1,
            weight=1,
        )


    def forgot_password(self) -> None:
        if self.on_forgot_password is not None:
            self.on_forgot_password()

    def credentials(
        self,
    ) -> tuple[str, str]:
        return (
            self.username_entry.get(),
            self.password_entry.get(),
        )

    def submit(
        self,
    ) -> None:
        if self.on_submit is not None:
            self.on_submit(
                self.credentials()
            )


class SetupForm(ttk.Frame):

    def __init__(
        self,
        master,
        *,
        on_submit=None,
    ) -> None:
        super().__init__(
            master,
        )
        self.on_submit = on_submit

        ttk.Label(
            self,
            text="Username",
            style="Garlic.TLabel",
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, 12),
            pady=3,
        )

        ttk.Label(
            self,
            text="Password",
            style="Garlic.TLabel",
        ).grid(
            row=1,
            column=0,
            sticky="w",
            padx=(0, 12),
            pady=3,
        )

        ttk.Label(
            self,
            text="Confirm password",
            style="Garlic.TLabel",
        ).grid(
            row=2,
            column=0,
            sticky="w",
            padx=(0, 12),
            pady=3,
        )

        self.username_entry = ttk.Entry(
            self,
        )

        self.username_entry.grid(
            row=0,
            column=1,
            sticky="ew",
            pady=3,
        )

        self.password_entry = ttk.Entry(
            self,
            show="*",
        )

        self.password_entry.grid(
            row=1,
            column=1,
            sticky="ew",
            pady=3,
        )

        self.password_confirmation_entry = ttk.Entry(
            self,
            show="*",
        )

        self.password_confirmation_entry.grid(
            row=2,
            column=1,
            sticky="ew",
            pady=3,
        )

        self.create_button = ttk.Button(
            self,
            text="Create account",
            command=self.submit,
        )

        self.create_button.grid(
            row=3,
            column=1,
            sticky="e",
            pady=(8, 0),
        )

        self.columnconfigure(
            1,
            weight=1,
        )

    def credentials(
        self,
    ) -> tuple[str, str, str]:
        return (
            self.username_entry.get(),
            self.password_entry.get(),
            self.password_confirmation_entry.get(),
        )

    def submit(
        self,
    ) -> None:
        if self.on_submit is not None:
            self.on_submit(
                self.credentials()
            )


class LoginDialog(tk.Toplevel):

    def __init__(
        self,
        master,
    ) -> None:
        super().__init__(
            master,
        )

        self.result = None

        self.form = LoginForm(
            self,
            on_submit=self.accept,
            on_forgot_password=self.forgot_password,
        )

        self.form.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        self.update_idletasks()

        x = (
            self.winfo_screenwidth()
            - self.winfo_width()
        ) // 2
        y = (
            self.winfo_screenheight()
            - self.winfo_height()
        ) // 2

        self.geometry(
            f"+{x}+{y}"
        )

    def accept(
        self,
        credentials,
    ) -> None:
        self.result = credentials
        self.destroy()

    def forgot_password(self) -> None:
        self.result = "forgot_password"
        self.destroy()

    def cancel(
        self,
    ) -> None:
        self.destroy()


class SetupDialog(tk.Toplevel):

    def __init__(
        self,
        master,
    ) -> None:
        super().__init__(
            master,
        )

        self.result = None

        self.form = SetupForm(
            self,
            on_submit=self.accept,
        )

        self.form.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

    def accept(
        self,
        credentials,
    ) -> None:
        self.result = credentials
        self.destroy()

    def cancel(
        self,
    ) -> None:
        self.destroy()

class RecoveryDialog(tk.Toplevel):

    def __init__(
        self,
        master,
        recovery_key: str,
    ) -> None:
        super().__init__(master)

        self.result = False
        self.recovery_key = recovery_key

        self.title("GarlicSMTP recovery key")

        self.warning_label = ttk.Label(
            self,
            text=(
                "Save your recovery key in a secure place.\n"
                "If you lose your password and recovery key, "
                "you may permanently lose access to your encrypted data."
            ),
            wraplength=500,
            justify="left",
        )

        self.warning_label.grid(
            row=0,
            column=0,
            padx=20,
            pady=(20, 10),
            sticky="w",
        )

        self.recovery_key_entry = ttk.Entry(
            self,
            width=68,
        )
        self.recovery_key_entry.insert(0, recovery_key)
        self.recovery_key_entry.configure(state="readonly")

        self.recovery_key_entry.grid(
            row=1,
            column=0,
            padx=20,
            pady=20,
            sticky="ew",
        )

        self.copy_button = ttk.Button(
            self,
            text="Copy recovery key",
            command=self.copy_recovery_key,
        )

        self.copy_button.grid(
            row=2,
            column=0,
            padx=20,
            pady=(0, 10),
        )

        self.reentry_label = ttk.Label(
            self,
            text="Re-enter your recovery key to confirm:",
        )
        self.reentry_label.grid(
            row=3,
            column=0,
            padx=20,
            pady=(10, 5),
            sticky="w",
        )

        self.reentry_entry = ttk.Entry(
            self,
            width=68,
        )
        self.reentry_entry.grid(
            row=4,
            column=0,
            padx=20,
            pady=(0, 10),
            sticky="ew",
        )

        self.confirm_button = ttk.Button(
            self,
            text="Verify recovery key",
            command=self.accept,
        )

        self.confirm_button.grid(
            row=5,
            column=0,
            padx=20,
            pady=(0, 20),
        )

        self.protocol(
            "WM_DELETE_WINDOW",
            self.cancel,
        )

    def copy_recovery_key(self) -> None:
        self.clipboard_clear()
        self.clipboard_append(self.recovery_key)

    def accept(self) -> None:
        entered_key = self.reentry_entry.get()
        if not entered_key:
            return

        self.result = entered_key
        self.destroy()

    def cancel(self) -> None:
        self.result = False
        self.destroy()

class PasswordResetDialog(tk.Toplevel):
    def __init__(self, master) -> None:
        super().__init__(master)

        self.result = None
        self.title("GarlicSMTP password recovery")

        fields = (
            ("Username", "username_entry", False),
            ("Existing recovery key", "recovery_key_entry", True),
            ("New password", "new_password_entry", True),
            ("Confirm new password", "password_confirmation_entry", True),
        )

        for row, (label, attribute, secret) in enumerate(fields):
            ttk.Label(
                self,
                text=label,
            ).grid(
                row=row,
                column=0,
                padx=(20, 12),
                pady=6,
                sticky="w",
            )

            entry = ttk.Entry(
                self,
                width=42,
                show="*" if secret else "",
            )
            entry.grid(
                row=row,
                column=1,
                padx=(0, 20),
                pady=6,
                sticky="ew",
            )
            setattr(self, attribute, entry)

        self.error_label = ttk.Label(
            self,
            text="",
            foreground="red",
        )
        self.error_label.grid(
            row=4,
            column=0,
            columnspan=2,
            padx=20,
            pady=6,
            sticky="w",
        )

        self.reset_button = ttk.Button(
            self,
            text="Continue",
            command=self.accept,
        )
        self.reset_button.grid(
            row=5,
            column=1,
            padx=20,
            pady=(8, 16),
            sticky="e",
        )

        self.cancel_button = ttk.Button(
            self,
            text="Cancel",
            command=self.cancel,
        )
        self.cancel_button.grid(
            row=5,
            column=0,
            padx=20,
            pady=(8, 16),
            sticky="w",
        )

        self.columnconfigure(1, weight=1)
        self.protocol("WM_DELETE_WINDOW", self.cancel)

    def accept(self) -> None:
        username = self.username_entry.get()
        recovery_key = self.recovery_key_entry.get()
        new_password = self.new_password_entry.get()
        confirmation = self.password_confirmation_entry.get()

        if not username or not recovery_key or not new_password:
            self.error_label.configure(
                text="All fields are required",
            )
            return

        if new_password != confirmation:
            self.error_label.configure(
                text="Passwords do not match",
            )
            return

        self.result = (
            username,
            recovery_key,
            new_password,
        )
        self.destroy()

    def cancel(self) -> None:
        self.result = None
        self.destroy()


def prompt_login(
    master,
):
    dialog = LoginDialog(
        master,
    )
    dialog.grab_set()
    dialog.wait_window()
    return dialog.result

def prompt_setup(
    master,
):
    dialog = SetupDialog(
        master,
    )
    dialog.grab_set()
    dialog.wait_window()
    return dialog.result