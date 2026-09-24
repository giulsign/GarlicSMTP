# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.


from tkinter import messagebox, ttk
from collections.abc import Callable

from garlicsmtp.application import (
    MessageFormatter,
    MessageListViewModel,
    MessageSummary,
)
from garlicsmtp.gui.tk_dashboard_widgets import (
    DashboardCard,
)



class MessageListSection(DashboardCard):

    COLUMN_STATUS = 0
    COLUMN_UID = 1
    COLUMN_SENDER = 2
    COLUMN_SUBJECT = 3
    COLUMN_DATE = 4
    COLUMN_SIZE = 5

    COLUMNS = (
        "status",
        "uid",
        "sender",
        "subject",
        "date",
        "size",
    )

    def __init__(
        self,
        master,
        *,
        view_model: MessageListViewModel,
        formatter: MessageFormatter | None = None,
    ) -> None:
        super().__init__(
            master,
            title="Messages",
        )

        self.view_model = view_model
        self.formatter = (
            formatter
            or MessageFormatter()
        )
        self._selection_listeners: list[
            Callable[[str], None]
        ] = []

        self._deleted_listeners: list[
            Callable[[str], None]
        ] = []

        self.toolbar_widget = ttk.Frame(
            self.content,
            style="Garlic.Card.TFrame",
        )
        self.toolbar_widget.grid(
            row=0,
            column=0,
            sticky="ew",
            pady=(0, 8),
        )

        self.refresh_button = ttk.Button(
            self.toolbar_widget,
            text="Refresh",
            command=self._refresh_messages,
        )
        self.refresh_button.grid(
            row=0,
            column=0,
            sticky="w",
        )

        self.mark_read_button = ttk.Button(
            self.toolbar_widget,
            text="Mark read",
            command=self._mark_selected_read,
        )
        self.mark_read_button.grid(
            row=0,
            column=1,
            sticky="w",
            padx=(8, 0),
        )

        self.mark_unread_button = ttk.Button(
            self.toolbar_widget,
            text="Mark unread",
            command=self._mark_selected_unread,
        )
        self.mark_unread_button.grid(
            row=0,
            column=2,
            sticky="w",
            padx=(8, 0),
        )

        self.delete_button = ttk.Button(
            self.toolbar_widget,
            text="Delete",
            command=self._delete_selected_message,
        )
        self.delete_button.grid(
            row=0,
            column=3,
            sticky="w",
            padx=(8, 0),
        )

        table_frame = ttk.Frame(
            self.content,
            style="Garlic.Card.TFrame",
        )

        table_frame.grid(
            row=1,
            column=0,
            sticky="nsew",
        )

        self.table = ttk.Treeview(
            table_frame,
            columns=self.COLUMNS,
            show="headings",
            selectmode="browse",
            style="Garlic.Treeview",
        )

        self.table.tag_configure(
            "unread",
            font=("", 10, "bold"),
        )

        self.table.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        self.table.bind(
            "<<TreeviewSelect>>",
            self._on_selection_changed,
        )

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.table.yview,
        )
        scrollbar.grid(
            row=0,
            column=1,
            sticky="ns",
        )

        self.table.configure(
            yscrollcommand=scrollbar.set,
        )

        headings = (
            "Status",
            "UID",
            "From",
            "Subject",
            "Date",
            "Size",
        )

        for column, heading in zip(
            self.COLUMNS,
            headings,
        ):
            self.table.heading(
                column,
                text=heading,
            )

        self.table.column(
            "status",
            width=50,
            stretch=False,
            anchor="center",
        )
        self.table.column(
            "uid",
            width=50,
            stretch=False,
            anchor="e",
        )
        self.table.column(
            "sender",
            width=110,
            stretch=True,
        )
        self.table.column(
            "subject",
            width=150,
            stretch=True,
        )
        self.table.column(
            "date",
            width=100,
            stretch=False,
        )
        self.table.column(
            "size",
            width=60,
            stretch=False,
            anchor="e",
        )

        self.content.columnconfigure(
            0,
            weight=1,
        )
        self.content.rowconfigure(
            1,
            weight=1,
        )

        table_frame.columnconfigure(
            0,
            weight=1,
        )
        table_frame.rowconfigure(
            0,
            weight=1,
        )

    @property
    def selected_message_id(
        self,
    ) -> str | None:
        selection = (
            self.table.selection()
        )

        if not selection:
            return None

        message_id = selection[0]

        if not isinstance(
            message_id,
            str,
        ):
            return None

        return message_id

    def add_selection_listener(
        self,
        listener: Callable[
            [str],
            None,
        ],
    ) -> None:
        self._selection_listeners.append(
            listener
        )

    def add_deleted_listener(
        self,
        listener: Callable[
            [str],
            None,
        ],
    ) -> None:
        self._deleted_listeners.append(
            listener
        )

    def _notify_deleted(
        self,
        message_id: str,
    ) -> None:
        for listener in tuple(
            self._deleted_listeners
        ):
            listener(
                message_id
            )

    def select_message(
        self,
        message_id: str,
    ) -> bool:
        if not self.table.exists(
            message_id
        ):
            return False

        if (
            self.selected_message_id
            == message_id
        ):
            return True

        if not self.view_model.select_message(
            message_id
        ):
            return False

        self.table.selection_set(
            message_id
        )
        self.table.focus(
            message_id
        )
        self.table.see(
            message_id
        )

        self._notify_selection(
            message_id
        )

        return True

    def _notify_selection(
        self,
        message_id: str,
    ) -> None:
        for listener in tuple(
            self._selection_listeners
        ):
            listener(
                message_id
            )

    def refresh_view(
        self,
    ) -> None:
        selected_message_id = (
            self.view_model
            .selected_message_id
        )

        for item_id in (
            self.table.get_children()
        ):
            self.table.delete(
                item_id
            )

        for message in (
            self.view_model.messages
        ):
            self._insert_message(
                message
            )

        if (
            selected_message_id
            is not None
            and self.table.exists(
                selected_message_id
            )
        ):
            self.table.selection_set(
                selected_message_id
            )
            self.table.focus(
                selected_message_id
            )
            self.table.see(
                selected_message_id
            )

    def _insert_message(
        self,
        message: MessageSummary,
    ) -> None:
        tags = ()

        if "\\Seen" not in message.flags:
            tags = ("unread",)

        self.table.insert(
            "",
            "end",
            iid=message.id,
            values=(
                self.formatter.format_status(
                    message
                ),
                str(message.uid),
                self.formatter.format_sender(
                    message
                ),
                self.formatter.format_subject(
                    message
                ),
                self.formatter.format_date(
                    message.internal_date
                ),
                self.formatter.format_size(
                    message.size
                ),
            ),
            tags=tags,
        )

    def _on_selection_changed(
        self,
        event,
    ) -> None:
        del event

        message_id = (
            self.selected_message_id
        )

        if message_id is None:
            self.view_model.select_message(
                None
            )
            return

        if (
            self.view_model
            .selected_message_id
            == message_id
        ):
            return

        if self.view_model.select_message(
            message_id
        ):
            self._notify_selection(
                message_id
            )

    def _refresh_messages(
        self,
    ) -> None:
        self.view_model.refresh()
        self.refresh_view()

    def _mark_selected_read(
        self,
    ) -> None:
        if self.view_model.mark_selected_read():
            self.view_model.refresh()
            self.refresh_view()

    def _mark_selected_unread(
        self,
    ) -> None:
        if self.view_model.mark_selected_unread():
            self.view_model.refresh()
            self.refresh_view()

    def _delete_selected_message(
        self,
    ) -> None:
        message_id = (
            self.view_model
            .selected_message_id
        )

        if message_id is None:
            return

        confirmed = messagebox.askyesno(
            "Delete message",
            "Delete the selected message?",
            parent=self.winfo_toplevel(),
        )

        if not confirmed:
            return

        if self.view_model.delete_selected():
            self.refresh_view()
            self._notify_deleted(
                message_id
            )
