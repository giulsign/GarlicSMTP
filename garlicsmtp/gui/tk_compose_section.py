# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import tkinter as tk
from tkinter import filedialog, ttk
from pathlib import Path

from garlicsmtp.smtp.mime import (
    MimeAttachment,
)
from garlicsmtp.application.compose_view_model import (
    ComposeViewModel,
)
from garlicsmtp.gui.tk_dashboard_widgets import (
    DashboardCard,
)


class ComposeSection(DashboardCard):

    def __init__(
        self,
        master,
        *,
        view_model: ComposeViewModel,
    ) -> None:
        super().__init__(
            master,
            title="Compose",
        )

        self.view_model = view_model

        form = ttk.Frame(
            self.content,
            style="Garlic.Card.TFrame",
        )
        form.grid(
            row=0,
            column=0,
            sticky="ew",
        )
        form.columnconfigure(
            1,
            weight=1,
        )

        ttk.Label(
            form,
            text="From",
            style="Garlic.TLabel",
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, 12),
            pady=3,
        )

        self.sender_input = ttk.Entry(
            form,
            style="Garlic.TEntry",
        )
        self.sender_input.grid(
            row=0,
            column=1,
            sticky="ew",
            pady=3,
        )

        ttk.Label(
            form,
            text="To",
            style="Garlic.TLabel",
        ).grid(
            row=1,
            column=0,
            sticky="w",
            padx=(0, 12),
            pady=3,
        )

        self.recipient_input = ttk.Entry(
            form,
            style="Garlic.TEntry",
        )
        self.recipient_input.grid(
            row=1,
            column=1,
            sticky="ew",
            pady=3,
        )

        ttk.Label(
            form,
            text="Subject",
            style="Garlic.TLabel",
        ).grid(
            row=2,
            column=0,
            sticky="w",
            padx=(0, 12),
            pady=3,
        )

        self.subject_input = ttk.Entry(
            form,
            style="Garlic.TEntry",
        )
        self.subject_input.grid(
            row=2,
            column=1,
            sticky="ew",
            pady=3,
        )

        self.body_input = tk.Text(
            self.content,
            height=10,
            wrap="word",
        )
        self.body_input.grid(
            row=1,
            column=0,
            sticky="nsew",
            pady=(8, 8),
        )

        self.attachment_label = ttk.Label(
            self.content,
            text="",
            style="Garlic.TLabel",
        )
        self.attachment_label.grid(
            row=2,
            column=0,
            sticky="w",
            pady=(0, 8),
        )

        actions = ttk.Frame(
            self.content,
            style="Garlic.Card.TFrame",
        )
        actions.grid(
            row=3   ,
            column=0,
            sticky="ew",
        )

        self.send_button = ttk.Button(
            actions,
            text="Send",
            command=self._send_message,
        )
        self.send_button.grid(
            row=0,
            column=0,
            sticky="w",
        )

        self.clear_button = ttk.Button(
            actions,
            text="Clear",
            command=self._clear_fields,
        )
        self.clear_button.grid(
            row=0,
            column=1,
            sticky="w",
            padx=(8, 0),
        )

        self.attach_button = ttk.Button(
            actions,
            text="Attach",
            command=self._select_attachment,
        )
        self.attach_button.grid(
            row=0,
            column=2,
            sticky="w",
            padx=(8, 0),
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
        self.sender_input.delete(
            0,
            tk.END,
        )
        self.sender_input.insert(
            0,
            self.view_model.sender,
        )

    def _send_message(
        self,
    ) -> None:
        self.view_model.sender = (
            self.sender_input.get()
        )

        self.view_model.recipient = (
            self.recipient_input.get()
        )

        self.view_model.subject = (
            self.subject_input.get()
        )

        self.view_model.body = (
            self.body_input.get(
                "1.0",
                "end-1c",
            )
        )

        try:
            sent = self.view_model.send()
        except Exception:
            return

        if sent:
            self._clear_fields()

    def _clear_fields(
        self,
    ) -> None:
        self.sender_input.delete(
            0,
            tk.END,
        )
        self.recipient_input.delete(
            0,
            tk.END,
        )
        self.subject_input.delete(
            0,
            tk.END,
        )
        self.body_input.delete(
            "1.0",
            tk.END,
        )

        self.view_model.attachments = []

        self.attachment_label.configure(
            text="",
        )

    def _attach_file(
        self,
        path,
    ) -> None:
        path = Path(path)

        mime_by_suffix = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".pdf": "application/pdf",
            ".txt": "text/plain",
        }

        declared_mime = mime_by_suffix.get(
            path.suffix.lower()
        )

        if declared_mime is None:
            raise ValueError(
                "Unsupported attachment type"
            )

        self.view_model.attachments.append(
            MimeAttachment(
                filename=path.name,
                declared_mime=declared_mime,
                content=path.read_bytes(),
            )
        )

        self.attachment_label.configure(
            text=path.name,
        )

    def _select_attachment(
        self,
    ) -> None:
        path = filedialog.askopenfilename(
            title="Attach file",
            filetypes=[
                (
                    "Supported files",
                    "*.jpg *.jpeg *.png *.pdf *.txt",
                ),
            ],
        )

        if not path:
            return

        self._attach_file(path)
