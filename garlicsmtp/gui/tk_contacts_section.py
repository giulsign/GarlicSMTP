
# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import tkinter as tk
from tkinter import ttk, messagebox

from garlicsmtp.gui.tk_dashboard_widgets import (
    DashboardCard,
)


class ContactsSection(DashboardCard):

    def __init__(
        self,
        master,
        *,
        view_model,
    ) -> None:
        super().__init__(
            master,
            title="Contacts",
        )

        self.view_model = view_model

        self.name_var = tk.StringVar(
            master=self,
        )

        self.address_var = tk.StringVar(
            master=self,
        )

        self.contacts_tree = ttk.Treeview(
            self.content,
            columns=(
                "name",
                "onion_address",
            ),
            show="headings",
            height=6,
            selectmode="browse",
        )

        self.contacts_tree.heading(
            "name",
            text="Name",
        )

        self.contacts_tree.heading(
            "onion_address",
            text="Onion address",
        )

        self.contacts_tree.column(
            "name",
            width=180,
            minwidth=100,
        )

        self.contacts_tree.column(
            "onion_address",
            width=350,
            minwidth=180,
        )

        self.contacts_tree.grid(
            row=0,
            column=0,
            columnspan=4,
            sticky="nsew",
            pady=(0, 10),
        )

        self.contacts_tree.bind(
            "<<TreeviewSelect>>",
            self._on_contact_selected,
        )

        ttk.Label(
            self.content,
            text="Name",
            style="Garlic.TLabel",
        ).grid(
            row=1,
            column=0,
            sticky="w",
            pady=3,
        )

        self.name_entry = ttk.Entry(
            self.content,
            textvariable=self.name_var,
        )

        self.name_entry.grid(
            row=1,
            column=1,
            columnspan=3,
            sticky="ew",
            pady=3,
        )

        ttk.Label(
            self.content,
            text="Onion address",
            style="Garlic.TLabel",
        ).grid(
            row=2,
            column=0,
            sticky="w",
            pady=3,
        )

        self.address_entry = ttk.Entry(
            self.content,
            textvariable=self.address_var,
        )

        self.address_entry.grid(
            row=2,
            column=1,
            columnspan=3,
            sticky="ew",
            pady=3,
        )

        self.add_button = ttk.Button(
            self.content,
            text="Add",
            command=self._add_contact,
        )

        self.update_button = ttk.Button(
            self.content,
            text="Update",
            command=self._update_contact,
        )

        self.delete_button = ttk.Button(
            self.content,
            text="Delete",
            command=self._delete_contact,
        )

        self.refresh_button = ttk.Button(
            self.content,
            text="Refresh",
            command=self._refresh_contacts,
        )

        for column, button in enumerate(
            (
                self.add_button,
                self.update_button,
                self.delete_button,
                self.refresh_button,
            )
        ):
            button.grid(
                row=3,
                column=column,
                sticky="ew",
                padx=3,
                pady=(10, 0),
            )

        for column in range(4):
            self.content.columnconfigure(
                column,
                weight=1,
            )

        self.content.rowconfigure(
            0,
            weight=1,
        )

        self.refresh_view()

    def refresh_view(
        self,
    ) -> None:
        for item in self.contacts_tree.get_children():
            self.contacts_tree.delete(item)

        for contact in self.view_model.contacts:
            self.contacts_tree.insert(
                "",
                "end",
                iid=str(contact["id"]),
                values=(
                    contact["name"],
                    contact["onion_address"],
                ),
            )

    def _on_contact_selected(
        self,
        _event=None,
    ) -> None:
        selection = (
            self.contacts_tree.selection()
        )

        if not selection:
            return

        contact_id = int(selection[0])

        for contact in self.view_model.contacts:
            if contact["id"] == contact_id:
                self.name_var.set(
                    contact["name"]
                )

                self.address_var.set(
                    contact["onion_address"]
                )

                return

    def _add_contact(
        self,
    ) -> None:
        try:
            self.view_model.add_contact(
                name=self.name_var.get(),
                onion_address=self.address_var.get(),
            )
        except (ValueError, OSError):
            messagebox.showerror(
                "Contacts error",
                "Unable to add contact",
                parent=self.winfo_toplevel(),
            )
            return

        self.refresh_view()
        self._clear_fields()

    def _update_contact(
        self,
    ) -> None:
        selection = (
            self.contacts_tree.selection()
        )

        if not selection:
            return

        try:
            self.view_model.update_contact(
                contact_id=int(selection[0]),
                name=self.name_var.get(),
                onion_address=self.address_var.get(),
            )
        except (ValueError, OSError):
            messagebox.showerror(
                "Contacts error",
                "Unable to update contact",
                parent=self.winfo_toplevel(),
            )
            return

        self.refresh_view()
        self._clear_fields()

    def _delete_contact(
        self,
    ) -> None:
        selection = (
            self.contacts_tree.selection()
        )

        if not selection:
            return

        confirmed = messagebox.askyesno(
            "Delete contact",
            "Delete the selected contact?",
            parent=self.winfo_toplevel(),
        )

        if not confirmed:
            return

        try:
            self.view_model.delete_contact(
                contact_id=int(selection[0]),
            )
        except (ValueError, OSError):
            messagebox.showerror(
                "Contacts error",
                "Unable to delete contact",
                parent=self.winfo_toplevel(),
            )
            return

        self.refresh_view()
        self._clear_fields()

    def _refresh_contacts(
        self,
    ) -> None:
        try:
            self.view_model.refresh()
        except (ValueError, OSError):
            messagebox.showerror(
                "Contacts error",
                "Unable to refresh contacts",
                parent=self.winfo_toplevel(),
            )
            return

        self.refresh_view()
        self._clear_fields()

    def _clear_fields(
        self,
    ) -> None:
        self.name_var.set("")
        self.address_var.set("")
