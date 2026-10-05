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

        self.columnconfigure(
            1,
            weight=1,
        )

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