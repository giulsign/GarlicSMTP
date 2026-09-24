# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import tkinter as tk
from tkinter import ttk

from garlicsmtp.application import (
    ApplicationActivityEntry,
    ApplicationViewModel,
)
from garlicsmtp.gui.tk_dashboard_widgets import (
    DashboardCard,
)


class ActivitySection(DashboardCard):

    DEFAULT_VISIBLE_LIMIT = 100

    def __init__(
        self,
        master,
        *,
        view_model: ApplicationViewModel,
        visible_limit: int = DEFAULT_VISIBLE_LIMIT,
    ) -> None:
        if visible_limit <= 0:
            raise ValueError(
                "visible_limit must be "
                "greater than zero"
            )

        super().__init__(
            master,
            title="Activity",
        )

        self.view_model = view_model
        self.visible_limit = visible_limit

        header = ttk.Frame(
            self.content,
            style="Garlic.Card.TFrame",
        )
        header.grid(
            row=0,
            column=0,
            sticky="ew",
            pady=(0, 8),
        )
        header.columnconfigure(
            0,
            weight=1,
        )

        self.summary_value = ttk.Label(
            header,
            text="No events",
            style="Garlic.TLabel",
        )
        self.summary_value.grid(
            row=0,
            column=0,
            sticky="w",
        )

        self.clear_button = ttk.Button(
            header,
            text="Clear",
            command=self.clear_activity,
            state="disabled",
        )
        self.clear_button.grid(
            row=0,
            column=1,
            sticky="e",
        )

        self.activity_list = tk.Listbox(
            self.content,
            exportselection=False,
            height=10,
        )
        self.activity_list.grid(
            row=1,
            column=0,
            sticky="nsew",
        )

        self.content.columnconfigure(
            0,
            weight=1,
        )
        self.content.rowconfigure(
            1,
            weight=1,
        )

    def refresh_view(
        self,
    ) -> None:
        entries = (
            self.view_model
            .activity_entries[
                :self.visible_limit
            ]
        )

        self.activity_list.delete(
            0,
            tk.END,
        )

        for entry in entries:
            self.activity_list.insert(
                tk.END,
                self._build_item_text(
                    entry
                ),
            )

        count = len(entries)

        if count == 0:
            summary = "No events"
        elif count == 1:
            summary = "1 event"
        else:
            summary = f"{count} events"

        self.summary_value.configure(
            text=summary
        )

        if count > 0:
            self.clear_button.state(
                ["!disabled"]
            )
        else:
            self.clear_button.state(
                ["disabled"]
            )

    def clear_activity(
        self,
    ) -> None:
        self.view_model.clear_activity()
        self.refresh_view()


    @staticmethod
    def _build_item_text(
        entry: ApplicationActivityEntry,
    ) -> str:
        return (
            f"{entry.timestamp_text}  "
            f"{entry.icon_text}  "
            f"{entry.source_text}  "
            f"{entry.short_text}"
        )
