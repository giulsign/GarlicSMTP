# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

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
            text="Personal Onion Page",
            padding=12,
        )

        self.preferences = preferences

        selection = self._try_load_initial_selection()

        
        custom_load_failed = self._preferences_load_failed
        custom_load_error = self._preferences_load_error

        website_selection = self._try_load_initial_website_selection()

        website_load_failed = self._preferences_load_failed
        website_load_error = self._preferences_load_error

        self._preferences_load_failed = (
            custom_load_failed or website_load_failed
        )
        self._preferences_load_error = (
            custom_load_error or website_load_error
        )

        if website_selection is None:
            website_enabled, website_html_path = False, ""
        else:
            website_enabled, website_html_path = website_selection

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
        
        self.website_enabled_var = tk.BooleanVar(
            master=self,
            value=website_enabled,
        )
        self.website_html_path_var = tk.StringVar(
            master=self,
            value=website_html_path,
        )

        ttk.Checkbutton(
            self,
            text="Enable custom presence HTML page",
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
            text="HTML file path:",
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
            text="Save preferences",
            command=self._on_save,
        )

        self.save_button.grid(
            row=2,
            column=1,
            sticky="e",
            pady=(12, 0),
        )

        ttk.Checkbutton(
            self,
            text="Enable Onion website",
            variable=self.website_enabled_var,
        ).grid(
            row=4,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(12, 8),
        )

        ttk.Label(
            self,
            text="Website HTML file:",
        ).grid(
            row=5,
            column=0,
            sticky="w",
            padx=(0, 8),
        )

        ttk.Entry(
            self,
            textvariable=self.website_html_path_var,
            width=42,
        ).grid(
            row=5,
            column=1,
            sticky="ew",
        )
        
        ttk.Button(
            self,
            text="Browse...",
            command=self._browse_website_html,
        ).grid(
            row=5,
            column=2,
            sticky="w",
            padx=(8, 0),
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

    def save_website_selection(
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
                "Cannot save Onion website preferences: "
                "configuration was not loaded successfully"
            )

        self.preferences.save_website(
            enabled=enabled,
            html_path=html_path,
        )

    def save_combined_selection(
        self,
        *,
        custom_enabled: bool,
        custom_html_path: str,
        website_enabled: bool,
        website_index_path: str,
    ) -> None:
        if self._preferences_load_failed:
            raise RuntimeError(
                "Cannot save Onion page preferences after a failed load"
            )

        self.preferences.save_combined(
            custom_enabled=custom_enabled,
            custom_html_path=custom_html_path,
            website_enabled=website_enabled,
            website_index_path=website_index_path,
        )

    def _on_save(self) -> None:
        try:
            
            website_enabled = self.website_enabled_var.get()
            website_html_path = self.website_html_path_var.get()

            if website_enabled and not website_html_path.strip():
                raise ValueError("Website HTML path is required")
            
            if website_enabled:
                website_file = Path(website_html_path).expanduser()

                if not website_file.is_absolute():
                    website_file = (
                        self.preferences.settings_path.absolute().parent
                        / website_file
                    )

                if not website_file.is_file():
                    raise ValueError(
                        "Website HTML file does not exist"
                    )

            self.save_combined_selection(
                custom_enabled=self.enabled_var.get(),
                custom_html_path=self.html_path_var.get(),
                website_enabled=website_enabled,
                website_index_path=website_html_path,
            )
        
        except (OSError, ValueError, TypeError, RuntimeError) as exc:

            messagebox.showerror(
                "Onion configuration error",
                str(exc),
                parent=self,
            )
            return

        messagebox.showinfo(
            "Preferences saved",
            "Onion page preferences have been saved.\n"
            "Changes will take effect when the service restarts.",
            parent=self,
        )

    def load_selection(self) -> tuple[bool, str]:
        return self.preferences.load()

    def load_website_selection(self) -> tuple[bool, str]:
        return self.preferences.load_website()

    def _browse_website_html(self) -> None:
        selected_path = filedialog.askopenfilename(
            parent=self,
            title="Select Onion website HTML file",
            filetypes=[
                ("HTML files", "*.html *.htm"),
                ("All files", "*.*"),
            ],
        )

        if selected_path:
            self.website_html_path_var.set(selected_path)

    def _load_initial_selection(self) -> tuple[bool, str]:
        self._preferences_load_failed = True

        selection = self.load_selection()

        self._preferences_load_failed = False
        return selection

    def _load_initial_website_selection(
        self,
    ) -> tuple[bool, str]:
        self._preferences_load_failed = True

        selection = self.load_website_selection()

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

    def _try_load_initial_website_selection(
        self,
    ) -> tuple[bool, str] | None:
        self._preferences_load_error = None

        try:
            selection = self._load_initial_website_selection()
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
            "Unable to load Onion configuration: "
            f"{self._preferences_load_error}. "
            "Saving disabled."
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