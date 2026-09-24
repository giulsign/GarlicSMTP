# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import tkinter as tk
from tkinter import ttk

from garlicsmtp.gui.tk_theme import (
    configure_garlic_theme,
)


class DashboardCard(ttk.Frame):

    def __init__(
        self,
        master,
        *,
        title: str,
    ):
        style = ttk.Style(master)
        configure_garlic_theme(style)

        super().__init__(
            master,
            style="Garlic.Card.TFrame",
            padding=12,
        )

        self.title = title

        self.title_label = ttk.Label(
            self,
            text=title,
            style="Garlic.CardTitle.TLabel",
        )
        self.title_label.grid(
            row=0,
            column=0,
            sticky="w",
        )

        self.content = ttk.Frame(
            self,
            style="Garlic.Card.TFrame",
        )
        self.content.grid(
            row=1,
            column=0,
            sticky="nsew",
            pady=(10, 0),
        )

        self.columnconfigure(
            0,
            weight=1,
        )
        self.rowconfigure(
            1,
            weight=1,
        )

    def add_row(
        self,
        row: int,
        label: str,
        value: ttk.Widget,
    ) -> None:
        ttk.Label(
            self.content,
            text=label,
            style="Garlic.TLabel",
        ).grid(
            row=row,
            column=0,
            sticky="w",
            padx=(0, 12),
            pady=3,
        )

        value.grid(
            row=row,
            column=1,
            sticky="ew",
            pady=3,
        )

        self.content.columnconfigure(
            1,
            weight=1,
        )


class SelectableValue(ttk.Entry):

    def __init__(
        self,
        master,
        *,
        text: str = "",
    ):
        self._value = tk.StringVar(
            master=master,
            value=text,
        )

        super().__init__(
            master,
            textvariable=self._value,
            state="readonly",
            style="Garlic.Readonly.TEntry",
        )

    def set_text(
        self,
        text: str,
    ) -> None:
        self._value.set(text)


class StatusBadge(SelectableValue):

    def __init__(
        self,
        master,
        *,
        text: str = "",
        status_key: str = "",
    ):
        super().__init__(
            master,
            text=text,
        )

        self.status_key = status_key

    def set_status(
        self,
        *,
        text: str,
        status_key: str,
    ) -> None:
        self.status_key = status_key
        self.set_text(text)


class MetricValue(ttk.Frame):

    def __init__(
        self,
        master,
        *,
        label: str,
    ) -> None:
        super().__init__(
            master,
            style="Garlic.Card.TFrame",
        )

        self.label = ttk.Label(
            self,
            text=label,
            style="Garlic.TLabel",
        )
        self.label.grid(
            row=0,
            column=0,
            sticky="w",
        )

        self.value = SelectableValue(
            self,
        )
        self.value.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(3, 0),
        )

        self.columnconfigure(
            0,
            weight=1,
        )

    def set_text(
        self,
        text: str,
    ) -> None:
        self.value.set_text(text)