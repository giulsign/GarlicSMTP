# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import tkinter as tk
from tkinter import ttk, messagebox
from queue import Empty, Queue

from garlicsmtp.application import (
    ApplicationViewModel,
)
from garlicsmtp.gui.tk_activity_section import (
    ActivitySection,
)
from garlicsmtp.gui.tk_application_section import (
    ApplicationSection,
)
from garlicsmtp.gui.tk_mail_metrics_section import (
    MailMetricsSection,
)
from garlicsmtp.gui.tk_mailbox_list_section import (
    MailboxListSection,
)
from garlicsmtp.gui.tk_message_list_section import (
    MessageListSection,
)
from garlicsmtp.gui.tk_message_preview_section import (
    MessagePreviewSection,
)
from garlicsmtp.gui.tk_services_section import (
    ServicesSection,
)
from garlicsmtp.gui.tk_tor_section import (
    TorSection,
)
from garlicsmtp.gui.tk_compose_section import (
    ComposeSection,
)
from garlicsmtp.gui.tk_dashboard_widgets import (
    StatusBadge,
)


class MainWindow(ttk.Frame):

    def __init__(
        self,
        master,
        view_model: ApplicationViewModel,
    ) -> None:
        super().__init__(
            master,
            style="Garlic.TFrame",
        )

        self.view_model = view_model

        self._refresh_queue = Queue()

        self._refresh_poll_after_id = None

        self.view_model.subscribe(
            self._queue_refresh
        )

        self.header_frame = ttk.Frame(
            self,
            style="Garlic.TFrame",
        )

        self.title_label = ttk.Label(
            self.header_frame,
            text="GarlicSMTP",
            style="Garlic.TLabel",
        )

        self.subtitle_label = ttk.Label(
            self.header_frame,
            text="Private mail infrastructure monitor",
            style="Garlic.TLabel",
        )

        self.runtime_badge = StatusBadge(
            self.header_frame,
        )

        self.action_frame = ttk.Frame(
            self,
            style="Garlic.TFrame",
        )

        self.content_container = ttk.Frame(
            self,
            style="Garlic.TFrame",
        )

        self.content_canvas = tk.Canvas(
            self.content_container,
            highlightthickness=0,
            borderwidth=0,
        )

        self.content_scrollbar = ttk.Scrollbar(
            self.content_container,
            orient="vertical",
            command=self.content_canvas.yview,
        )

        self.content_canvas.configure(
            yscrollcommand=self.content_scrollbar.set,
        )

        self.content_frame = ttk.Frame(
            self.content_canvas,
            style="Garlic.TFrame",
        )

        self._content_window = (
            self.content_canvas.create_window(
                (0, 0),
                window=self.content_frame,
                anchor="nw",
            )
        )

        self.content_frame.bind(
            "<Configure>",
            self._update_content_scrollregion,
        )

        self.content_canvas.bind(
            "<Configure>",
            self._resize_content_frame,
        )

        self.content_canvas.bind(
            "<Button-4>",
            self._on_mouse_wheel_up,
        )

        self.content_canvas.bind(
            "<Button-5>",
            self._on_mouse_wheel_down,
        )

        self.compose_section = None

        if self.view_model.compose is not None:
            self.compose_section = ComposeSection(
                self.content_frame,
                view_model=self.view_model.compose,
            )

        self.application_section = ApplicationSection(
            self.content_frame,
            view_model=self.view_model,
        )

        self.services_section = ServicesSection(
            self.content_frame,
            view_model=self.view_model,
        )

        self.tor_section = TorSection(
            self.content_frame,
            view_model=self.view_model,
        )

        self.mailbox_section = MailboxListSection(
            self.content_frame,
            view_model=self.view_model,
        )

        self.mail_metrics_section = MailMetricsSection(
            self.content_frame,
            view_model=self.view_model,
        )

        self.activity_section = ActivitySection(
            self.content_frame,
            view_model=self.view_model,
        )

        self.messages_pane = ttk.Frame(
            self.content_frame,
            style="Garlic.TFrame",
        )

        self.message_list_section = MessageListSection(
            self.messages_pane,
            view_model=self.view_model.message_list,
        )

        self.message_preview_section = MessagePreviewSection(
            self.messages_pane,
            view_model=self.view_model.message_preview,
        )

        self.mailbox_section.add_selection_listener(
            self._select_mailbox
        )

        self.message_list_section.add_selection_listener(
            self._select_message
        )

        self.message_list_section.add_deleted_listener(
            self._message_deleted
        )

        self.refresh_button = ttk.Button(
            self.action_frame,
            text="Refresh",
            command=lambda: self._refresh(),
        )

        self.start_button = ttk.Button(
            self.action_frame,
            text="Start",
            command=lambda: self._start(),
        )

        self.stop_button = ttk.Button(
            self.action_frame,
            text="Stop",
            command=lambda: self._stop(),
        )

        self.restart_button = ttk.Button(
            self.action_frame,
            text="Restart",
            command=lambda: self._restart(),
        )

        self.application_section.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        self.services_section.grid(
            row=0,
            column=1,
            sticky="nsew",
        )

        self.tor_section.grid(
            row=0,
            column=2,
            sticky="nsew",
        )

        self.mailbox_section.grid(
            row=1,
            column=0,
            sticky="nsew",
        )

        self.mail_metrics_section.grid(
            row=1,
            column=1,
            sticky="nsew",
        )

        self.activity_section.grid(
            row=1,
            column=2,
            sticky="nsew",
        )

        for column in range(3):
            self.content_frame.columnconfigure(
                column,
                weight=1,
            )

        messages_row = 2

        if self.compose_section is not None:
            self.compose_section.grid(
                row=2,
                column=0,
                columnspan=3,
                sticky="nsew",
            )
            messages_row = 3

        self.message_list_section.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        self.message_preview_section.grid(
            row=0,
            column=1,
            sticky="nsew",
        )

        self.messages_pane.grid(
            row=messages_row,
            column=0,
            columnspan=3,
            sticky="nsew",
        )

        self.messages_pane.columnconfigure(
            0,
            weight=1,
        )

        self.messages_pane.columnconfigure(
            1,
            weight=2,
        )

        self.messages_pane.rowconfigure(
            0,
            weight=1,
        )

        self._bind_content_mouse_wheel(
            self.content_frame
        )

        self.content_frame.rowconfigure(
            messages_row,
            weight=1,
        )

        self.header_frame.grid(
            row=0,
            column=0,
            sticky="ew",
        )

        self.title_label.grid(
            row=0,
            column=0,
            sticky="w",
        )

        self.subtitle_label.grid(
            row=1,
            column=0,
            sticky="w",
        )

        self.runtime_badge.grid(
            row=0,
            column=1,
            rowspan=2,
            sticky="e",
        )

        self.header_frame.columnconfigure(
            0,
            weight=1,
        )

        self.content_container.grid(
            row=1,
            column=0,
            sticky="nsew",
        )

        self.content_canvas.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        self.content_scrollbar.grid(
            row=0,
            column=1,
            sticky="ns",
        )

        self.content_container.columnconfigure(
            0,
            weight=1,
        )

        self.content_container.rowconfigure(
            0,
            weight=1,
        )

        self.action_frame.grid(
            row=2,
            column=0,
            sticky="ew",
        )

        self.start_button.grid(
            row=0,
            column=0,
        )

        self.stop_button.grid(
            row=0,
            column=1,
        )

        self.restart_button.grid(
            row=0,
            column=2,
        )

        self.refresh_button.grid(
            row=0,
            column=4,
        )

        self.action_frame.columnconfigure(
            3,
            weight=1,
        )

        self.columnconfigure(
            0,
            weight=1,
        )

        self.rowconfigure(
            1,
            weight=1,
        )


        self.refresh_view()

        self._schedule_refresh_poll()

    def _update_content_scrollregion(
        self,
        _event=None,
    ) -> None:
        self.content_canvas.configure(
            scrollregion=(
                self.content_canvas.bbox("all")
            ),
        )


    def _resize_content_frame(
        self,
        event,
    ) -> None:
        self.content_canvas.itemconfigure(
            self._content_window,
            width=event.width,
        )


    def _on_mouse_wheel_up(
        self,
        _event,
    ) -> None:
        self.content_canvas.yview_scroll(
            -1,
            "units",
        )

    def _on_mouse_wheel_down(
        self,
        _event,
    ) -> None:
        self.content_canvas.yview_scroll(
            1,
            "units",
        )

    def _bind_content_mouse_wheel(
        self,
        widget,
    ) -> None:
        widget.bind(
            "<Button-4>",
            self._on_mouse_wheel_up,
            add="+",
        )
        widget.bind(
            "<Button-5>",
            self._on_mouse_wheel_down,
            add="+",
        )

        for child in widget.winfo_children():
            self._bind_content_mouse_wheel(
                child
            )

    def _refresh_sections(self) -> None:
        sections = (
            self.application_section,
            self.services_section,
            self.tor_section,
            self.mailbox_section,
            self.mail_metrics_section,
            self.activity_section,
            self.message_list_section,
            self.message_preview_section,
        )

        for section in sections:
            section.refresh_view()

        if self.compose_section is not None:
            self.compose_section.refresh_view()

    def _select_mailbox(
        self,
        mailbox: str,
    ) -> None:
        self.view_model.message_list.select_mailbox(
            mailbox
        )

        self.view_model.message_preview.select_message(
            mailbox=mailbox,
            message_id=None,
        )

        self.message_list_section.refresh_view()
        self.message_preview_section.refresh_view()

    def _select_message(
        self,
        message_id: str,
    ) -> None:
        mailbox = (
            self.view_model
            .message_list
            .selected_mailbox
        )

        if mailbox is None:
            return

        self.view_model.message_preview.select_message(
            mailbox=mailbox,
            message_id=message_id,
        )

        self.message_preview_section.refresh_view()

    def _message_deleted(
        self,
        message_id: str,
    ) -> None:
        if (
            self.view_model
            .message_preview
            .message_id
            != message_id
        ):
            return

        mailbox = (
            self.view_model
            .message_list
            .selected_mailbox
        )

        self.view_model.message_preview.select_message(
            mailbox=mailbox,
            message_id=None,
        )

        self.message_preview_section.refresh_view()

    def refresh_view(
        self,
    ) -> None:
        self._refresh_sections()

        self.runtime_badge.set_status(
            text=self.view_model.runtime_text,
            status_key=(
                self.view_model.runtime_status_key
            ),
        )

        self._refresh_action_buttons()

    def _refresh_action_buttons(
        self,
    ) -> None:
        self.start_button.state(
            [
                "!disabled"
                if self.view_model.can_start
                else "disabled"
            ]
        )

        self.stop_button.state(
            [
                "!disabled"
                if self.view_model.can_stop
                else "disabled"
            ]
        )

        self.restart_button.state(
            [
                "!disabled"
                if self.view_model.can_restart
                else "disabled"
            ]
        )

    def _start(
        self,
    ) -> None:
        self._execute_action(
            self.view_model.start
        )


    def _stop(
        self,
    ) -> None:
        self._execute_action(
            self.view_model.stop
        )


    def _restart(
        self,
    ) -> None:
        self._execute_action(
            self.view_model.restart
        )

    def _execute_action(
        self,
        action,
    ) -> None:
        try:
            action()

        except Exception:
            messagebox.showerror(
                "GarlicSMTP error",
                "Operation failed",
                parent=self.winfo_toplevel(),
            )

        self.refresh_view()

    def _refresh(
        self,
    ) -> None:
        self._execute_action(
            self.view_model.refresh
        )

    def _queue_refresh(
        self,
    ) -> None:
        self._refresh_queue.put(
            None
        )

    def _process_pending_refreshes(
        self,
    ) -> None:
        refresh_requested = False

        while True:
            try:
                self._refresh_queue.get_nowait()
            except Empty:
                break

            refresh_requested = True

        if refresh_requested:
            self.refresh_view()

        self._schedule_refresh_poll()

    def _schedule_refresh_poll(
        self,
    ) -> None:
        self._refresh_poll_after_id = (
            self.after(
                100,
                self._process_pending_refreshes,
            )
        )

    def close(
        self,
    ) -> None:
        if self._refresh_poll_after_id is not None:
            self.after_cancel(
                self._refresh_poll_after_id
            )

            self._refresh_poll_after_id = None

        self.view_model.unsubscribe(
            self._queue_refresh
        )

        if self.view_model.is_running:
            self.view_model.stop()

        self.view_model.close()