# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import tkinter as tk
from collections.abc import Callable
from tkinter import messagebox, ttk

from garlicsmtp.application import (
    ApplicationViewModel,
)
from garlicsmtp.gui.tk_dashboard_widgets import (
    DashboardCard,
)


class MailboxListSection(DashboardCard):

    def __init__(
        self,
        master,
        *,
        view_model: ApplicationViewModel,
    ) -> None:
        super().__init__(
            master,
            title="Mailboxes",
        )

        self.view_model = view_model
        self.custom_addresses_var = tk.BooleanVar(
            master=self,
            value=self.view_model.custom_addresses_enabled,
        )

        self.custom_addresses_checkbox = ttk.Checkbutton(
            self,
            text="Indirizzi personalizzati",
            variable=self.custom_addresses_var,
            command=self._on_custom_addresses_changed,
        )

        self.custom_addresses_checkbox.grid(
            row=0,
            column=1,
            sticky="e",
            padx=(12, 0),
        )

        self.content.grid_configure(
            columnspan=2,
        )

        self.columnconfigure(
            1,
            weight=0,
        )
        self._addresses: list[str] = []
        self._selection_listeners: list[
            Callable[[str], None]
        ] = []

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
            text="No mailboxes",
            style="Garlic.TLabel",
        )
        self.summary_value.grid(
            row=0,
            column=0,
            sticky="w",
        )

        self.refresh_button = ttk.Button(
            header,
            text="Refresh",
            command=self.refresh_mailboxes,
        )
        self.refresh_button.grid(
            row=0,
            column=1,
            sticky="e",
        )

        self.mailbox_list = tk.Listbox(
            self.content,
            exportselection=False,
            height=8,
        )
        self.mailbox_list.grid(
            row=1,
            column=0,
            sticky="nsew",
        )

        self.mailbox_list.bind(
            "<<ListboxSelect>>",
            self._on_selection_changed,
        )

        self.content.columnconfigure(
            0,
            weight=1,
        )
        self.content.rowconfigure(
            1,
            weight=1,
        )

    def _on_custom_addresses_changed(self) -> None:
        requested = self.custom_addresses_var.get()

        if requested:
            confirmed = messagebox.askyesno(
                "Abilitare indirizzi personalizzati?",
                (
                    "Vuoi consentire indirizzi email personalizzati "
                    "per questa sessione?\n\n"
                    "Per impostazione predefinita è consentito "
                    "soltanto garlicsmtp@<tuo-onion>.onion.\n\n"
                    "Questa opzione non modifica le mailbox esistenti "
                    "e verrà disattivata al prossimo avvio."
                ),
                parent=self.winfo_toplevel(),
            )

            if not confirmed:
                self.custom_addresses_var.set(
                    self.view_model.custom_addresses_enabled
                )
                return

        try:
            self.view_model.set_custom_addresses_enabled(requested)
        finally:
            self.custom_addresses_var.set(
                self.view_model.custom_addresses_enabled
            )

    @property
    def selected_mailbox(
        self,
    ) -> str | None:
        selection = (
            self.mailbox_list.curselection()
        )

        if not selection:
            return None

        index = selection[0]

        if index >= len(self._addresses):
            return None

        return self._addresses[index]

    def add_selection_listener(
        self,
        listener: Callable[[str], None],
    ) -> None:
        self._selection_listeners.append(
            listener
        )

    def refresh_view(
        self,
    ) -> None:
        selected_mailbox = (
            self.selected_mailbox
        )

        items = self.view_model.mailbox_items

        self.mailbox_list.delete(
            0,
            tk.END,
        )
        self._addresses.clear()

        selected_index = None

        for index, mailbox in enumerate(items):
            self.mailbox_list.insert(
                tk.END,
                mailbox.display_text,
            )
            self._addresses.append(
                mailbox.address
            )

            if (
                mailbox.address
                == selected_mailbox
            ):
                selected_index = index

        if selected_index is not None:
            self.mailbox_list.selection_set(
                selected_index
            )
            self.mailbox_list.activate(
                selected_index
            )

        self._update_summary(items)

    def refresh_mailboxes(
        self,
    ) -> None:
        self.view_model.refresh()
        self.refresh_view()

    def select_mailbox(
        self,
        address: str,
    ) -> bool:
        try:
            index = self._addresses.index(
                address
            )
        except ValueError:
            return False

        self.mailbox_list.selection_clear(
            0,
            tk.END,
        )
        self.mailbox_list.selection_set(
            index
        )
        self.mailbox_list.activate(
            index
        )
        self.mailbox_list.see(
            index
        )

        self._notify_selection(
            address
        )

        return True

    def _update_summary(
        self,
        items,
    ) -> None:
        mailbox_count = len(items)
        message_count = sum(
            item.message_count
            for item in items
        )

        if mailbox_count == 0:
            text = "No mailboxes"
        else:
            mailbox_label = (
                "mailbox"
                if mailbox_count == 1
                else "mailboxes"
            )
            message_label = (
                "message"
                if message_count == 1
                else "messages"
            )

            text = (
                f"{mailbox_count} "
                f"{mailbox_label}, "
                f"{message_count} "
                f"{message_label}"
            )

        self.summary_value.configure(
            text=text
        )

    def _on_selection_changed(
        self,
        event,
    ) -> None:
        del event

        mailbox = self.selected_mailbox

        if mailbox is not None:
            self._notify_selection(
                mailbox
            )

    def _notify_selection(
        self,
        mailbox: str,
    ) -> None:
        for listener in tuple(
            self._selection_listeners
        ):
            listener(mailbox)
