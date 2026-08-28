# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from garlicsmtp.application.compose_view_model import (
    ComposeViewModel,
)
from garlicsmtp.gui.dashboard_widgets import (
    DashboardCard,
)


class ComposeSection(DashboardCard):

    def __init__(
        self,
        *,
        view_model: ComposeViewModel,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            "Compose",
            parent=parent,
        )

        self.view_model = view_model

        form_widget = QWidget(
            self
        )

        form_layout = QFormLayout(
            form_widget
        )

        form_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.sender_input = QLineEdit(
            form_widget
        )

        self.recipient_input = QLineEdit(
            form_widget
        )

        self.subject_input = QLineEdit(
            form_widget
        )

        self.body_input = QPlainTextEdit(
            self
        )

        self.body_input.setMinimumHeight(
            180
        )

        form_layout.addRow(
            "From",
            self.sender_input,
        )

        form_layout.addRow(
            "To",
            self.recipient_input,
        )

        form_layout.addRow(
            "Subject",
            self.subject_input,
        )

        actions_widget = QWidget(
            self
        )

        actions_layout = QHBoxLayout(
            actions_widget
        )

        actions_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.send_button = QPushButton(
            "Send",
            actions_widget,
        )

        self.clear_button = QPushButton(
            "Clear",
            actions_widget,
        )

        self.send_button.clicked.connect(
            self._send_message
        )

        self.clear_button.clicked.connect(
            self._clear_fields
        )

        actions_layout.addWidget(
            self.send_button
        )

        actions_layout.addWidget(
            self.clear_button
        )

        actions_layout.addStretch()

        self.add_widget(
            form_widget
        )

        self.add_widget(
            self.body_input
        )

        self.add_widget(
            actions_widget
        )

    def _send_message(
        self,
    ) -> None:
        self.view_model.sender = (
            self.sender_input.text()
        )

        self.view_model.recipient = (
            self.recipient_input.text()
        )

        self.view_model.subject = (
            self.subject_input.text()
        )

        self.view_model.body = (
            self.body_input.toPlainText()
        )

        if self.view_model.send():
            self._clear_fields()   

    def _clear_fields(
        self,
    ) -> None:
        self.sender_input.clear()
        self.recipient_input.clear()
        self.subject_input.clear()
        self.body_input.clear() 

    def refresh_view(
        self,
    ) -> None:
        self.sender_input.setText(
            self.view_model.sender
        )
