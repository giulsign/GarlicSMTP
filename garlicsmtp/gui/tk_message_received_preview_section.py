# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import tkinter as tk
from tkinter import ttk

from garlicsmtp.gui.tk_theme import (
    GarlicTheme,
)
from garlicsmtp.application import (
    MessagePreviewViewModel,
)
from garlicsmtp.gui.tk_dashboard_widgets import (
    DashboardCard,
    SelectableValue,
)


class MessageReceivedPreviewSection(DashboardCard):

    field_labels = (
        "From",
        "To",
        "Subject",
        "Size",
        "Date",
        "UID",
        "Flags",
    )

    def __init__(
        self,
        master,
        *,
        view_model: MessagePreviewViewModel,
        folder_opener,
        attachment_directory_factory,
    ) -> None:
        super().__init__(
            master,
            title="Message Received Preview",
        )

        self.view_model = view_model
        self.folder_opener = folder_opener
        self.attachment_directory_factory = (
            attachment_directory_factory
        )

        self.view_model = view_model

        self.placeholder_value = ttk.Label(
            self.content,
            text="",
            style="Garlic.TLabel",
            wraplength=500,
        )
        self.placeholder_value.grid(
            row=0,
            column=0,
            sticky="ew",
        )

        self.details_widget = ttk.Frame(
            self.content,
            style="Garlic.Card.TFrame",
        )

        self.header_widget = ttk.Frame(
            self.details_widget,
            style="Garlic.Card.TFrame",
        )
        self.header_widget.grid(
            row=0,
            column=0,
            sticky="ew",
        )
        self.header_widget.columnconfigure(
            1,
            weight=1,
        )

        self.sender_value = SelectableValue(
            self.header_widget
        )
        self.recipients_value = SelectableValue(
            self.header_widget
        )
        self.subject_value = SelectableValue(
            self.header_widget
        )
        self.size_value = SelectableValue(
            self.header_widget
        )
        self.date_value = SelectableValue(
            self.header_widget
        )
        self.uid_value = SelectableValue(
            self.header_widget
        )
        self.flags_value = SelectableValue(
            self.header_widget
        )

        values = (
            self.sender_value,
            self.recipients_value,
            self.subject_value,
            self.size_value,
            self.date_value,
            self.uid_value,
            self.flags_value,
        )

        for row, (
            label_text,
            value,
        ) in enumerate(
            zip(
                self.field_labels,
                values,
            )
        ):
            label = ttk.Label(
                self.header_widget,
                text=label_text,
                style="Garlic.Header.TLabel",
            )
            label.grid(
                row=row,
                column=0,
                sticky="w",
                padx=(0, 12),
                pady=2,
            )

            value.grid(
                row=row,
                column=1,
                sticky="ew",
                pady=2,
            )

        self.header_separator = ttk.Separator(
            self.details_widget,
            orient="horizontal",
        )
        self.header_separator.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(
                8,
                8,
            ),
        )

        self.attachment_value = ttk.Label(
            self.details_widget,
            text="",
            style="Garlic.TLabel",
        )
        self.attachment_value.grid(
            row=3,
            column=0,
            sticky="w",
            pady=(0, 8),
        )

        self.open_attachments_button = ttk.Button(
            self.details_widget,
            text="Open attachments folder",
            command=self._open_attachments_folder,
        )
        self.open_attachments_button.grid(
            row=4,
            column=0,
            sticky="w",
            pady=(0, 8),
        )

        self.body_value = tk.Text(
            self.details_widget,
            height=14,
            wrap="word",
            state="disabled",
            background=(
                GarlicTheme.INPUT_BACKGROUND
            ),
            foreground=(
                GarlicTheme.INPUT_FOREGROUND
            ),
            selectbackground=(
                GarlicTheme.SELECTION_BACKGROUND
            ),
        )

        self.body_value.grid(
            row=5,
            column=0,
            sticky="nsew",
        )

        self.details_widget.columnconfigure(
            0,
            weight=1,
        )
        self.details_widget.rowconfigure(
            5,
            weight=1,
        )

        self.content.columnconfigure(
            0,
            weight=1,
        )
        self.content.rowconfigure(
            1,
            weight=1,
        )

        self.refresh_view()

    def _open_attachments_folder(
        self,
    ) -> None:
        message_id = (
            self.view_model.message_id
        )

        if message_id is None:
            return

        destination = (
            self.attachment_directory_factory(
                message_id
            )
        )

        directory = (
            self.view_model
            .materialize_attachments(
                destination
            )
        )

        if directory is None:
            return

        self.folder_opener.open(
            directory
        )

    def refresh_view(
        self,
    ) -> None:
        if not self.view_model.has_message:
            self.placeholder_value.configure(
                text=(
                    self.view_model
                    .placeholder_text
                )
            )

            self.placeholder_value.grid(
                row=0,
                column=0,
                sticky="ew",
            )

            self.details_widget.grid(
                row=1,
                column=0,
                sticky="nsew",
            )

            self._clear_fields()
            return

        self.placeholder_value.grid_forget()

        self.details_widget.grid(
            row=1,
            column=0,
            sticky="nsew",
        )

        self.header_widget.grid()
        self.header_separator.grid()

        self.sender_value.set_text(
            self.view_model.sender
        )
        self.recipients_value.set_text(
            self.view_model.recipients_text
        )
        self.subject_value.set_text(
            self.view_model.subject
        )
        self.size_value.set_text(
            self.view_model.size_text
        )
        self.date_value.set_text(
            self.view_model.internal_date_text
        )
        self.uid_value.set_text(
            self.view_model.uid_text
        )
        self.flags_value.set_text(
            self.view_model.flags_text
        )

        attachments = self.view_model.attachments

        self.attachment_value.configure(
            text=", ".join(
                attachment.filename
                for attachment in attachments
            )
        )

        self._set_body_text(
            self.view_model.display_body
        )

    def _clear_fields(
        self,
    ) -> None:
        for value in (
            self.sender_value,
            self.recipients_value,
            self.subject_value,
            self.size_value,
            self.date_value,
            self.uid_value,
            self.flags_value,
        ):
            value.set_text("")

        self.attachment_value.configure(
            text=""
        )
        self._set_body_text("")

    def _set_body_text(
        self,
        text: str,
    ) -> None:
        self.body_value.configure(
            state="normal"
        )
        self.body_value.delete(
            "1.0",
            tk.END,
        )
        self.body_value.insert(
            "1.0",
            text,
        )
        self.body_value.configure(
            state="disabled"
        )
