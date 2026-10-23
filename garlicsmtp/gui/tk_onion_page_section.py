# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import tkinter as tk
from tkinter import messagebox, ttk

from garlicsmtp.gui.onion_page_preferences import (
    OnionPagePreferences,
)


class OnionPageSection(ttk.LabelFrame):
    def __init__(
        self,
        parent,
        *,
        preferences: OnionPagePreferences,
    ) -> None:
        super().__init__(
            parent,
            text="Pagina personale Onion",
            padding=12,
        )

        self.preferences = preferences

        selection = self._try_load_initial_selection()

        if selection is None:
            enabled, html_path = False, ""
        else:
            enabled, html_path = selection

        self.enabled_var = tk.BooleanVar(
            master=self,
            value=enabled,
        )
        self.html_path_var = tk.StringVar(
            master=self,
            value=html_path,
        )

        ttk.Checkbutton(
            self,
            text="Abilita pagina HTML personalizzata",
            variable=self.enabled_var,
        ).grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(0, 8),
        )

        ttk.Label(
            self,
            text="Percorso file HTML:",
        ).grid(
            row=1,
            column=0,
            sticky="w",
            padx=(0, 8),
        )

        ttk.Entry(
            self,
            textvariable=self.html_path_var,
            width=42,
        ).grid(
            row=1,
            column=1,
            sticky="ew",
        )

        self.save_button = ttk.Button(
            self,
            text="Salva preferenze",
            command=self._on_save,
        )

        self.save_button.grid(
            row=2,
            column=1,
            sticky="e",
            pady=(12, 0),
        )

        self._update_save_button_state()
        self._create_load_error_label()

        self.columnconfigure(1, weight=1)

        self.columnconfigure(1, weight=1)

    def save_selection(
        self,
        *,
        enabled: bool,
        html_path: str,
    ) -> None:
        if getattr(
            self,
            "_preferences_load_failed",
            False,
        ):
            raise RuntimeError(
                "Cannot save Onion page preferences: "
                "configuration was not loaded successfully"
            )

        self.preferences.save(
            enabled=enabled,
            html_path=html_path,
        )

    def _on_save(self) -> None:
        try:
            self.save_selection(
                enabled=self.enabled_var.get(),
                html_path=self.html_path_var.get(),
            )
        except (OSError, ValueError, TypeError) as exc:
            messagebox.showerror(
                "Errore configurazione Onion",
                str(exc),
                parent=self,
            )
            return

        messagebox.showinfo(
            "Preferenze salvate",
            "Le preferenze della pagina Onion sono state salvate.\n"
            "Saranno applicate al prossimo avvio del servizio.",
            parent=self,
        )

    def load_selection(self) -> tuple[bool, str]:
        return self.preferences.load()

    def _load_initial_selection(self) -> tuple[bool, str]:
        self._preferences_load_failed = True

        selection = self.load_selection()

        self._preferences_load_failed = False
        return selection

    def _try_load_initial_selection(
        self,
    ) -> tuple[bool, str] | None:
        self._preferences_load_error = None

        try:
            selection = self._load_initial_selection()
        except (OSError, ValueError, TypeError) as exc:
            self._preferences_load_failed = True
            self._preferences_load_error = str(exc)
            return None

        return selection

    def _update_save_button_state(self) -> None:
        if self._preferences_load_failed:
            self.save_button.state(["disabled"])
        else:
            self.save_button.state(["!disabled"])

    def _load_error_message(self) -> str:
        if self._preferences_load_error is None:
            return ""

        return (
            "Impossibile caricare la configurazione Onion: "
            f"{self._preferences_load_error}. "
            "Salvataggio disabilitato."
        )

    def _create_load_error_label(self) -> None:
        message = self._load_error_message()

        if not message:
            return

        ttk.Label(
            self,
            text=message,
            foreground="red",
            wraplength=420,
            justify="left",
        ).grid(
            row=3,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(8, 0),
        )