# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from PySide6.QtWidgets import (
    QFormLayout,
    QLabel,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from garlicsmtp.application import (
    MessagePreviewViewModel,
)
from garlicsmtp.gui.dashboard_widgets import (
    DashboardCard,
)
from PySide6.QtWidgets import (
    QFormLayout,
    QFrame,
    QLabel,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)


class MessagePreviewSection(DashboardCard):

    def __init__(
        self,
        *,
        view_model: MessagePreviewViewModel,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            "Message Preview",
            parent=parent,
        )

        self.view_model = view_model

        self.placeholder_value = QLabel()

        self.placeholder_value.setWordWrap(
            True
        )

        self.details_widget = QWidget(
            self
        )

        details_layout = QVBoxLayout(
            self.details_widget
        )

        details_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        details_layout.setSpacing(
            10
        )

        self.header_widget = QWidget(
            self.details_widget
        )

        header_layout = QFormLayout(
            self.header_widget
        )

        header_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.sender_value = QLabel()
        self.recipients_value = QLabel()
        self.subject_value = QLabel()
        self.size_value = QLabel()
        self.date_value = QLabel()
        self.uid_value = QLabel()
        self.flags_value = QLabel()

        for label in (
            self.sender_value,
            self.recipients_value,
            self.subject_value,
            self.date_value,
            self.uid_value,
            self.flags_value,
        ):
            label.setWordWrap(
                True
            )

        header_layout.addRow(
            self._make_field_label("From"),
            self.sender_value,
        )

        header_layout.addRow(
            self._make_field_label("To"),
            self.recipients_value,
        )

        header_layout.addRow(
            self._make_field_label("Subject"),
            self.subject_value,
        )

        header_layout.addRow(
            self._make_field_label("Size"),
            self.size_value,
        )

        header_layout.addRow(
            self._make_field_label("Date"),
            self.date_value,
        )

        header_layout.addRow(
            self._make_field_label("UID"),
            self.uid_value,
        )

        header_layout.addRow(
            self._make_field_label("Flags"),
            self.flags_value,
        )

        self.header_separator = QFrame(
            self.details_widget
        )

        self.header_separator.setFrameShape(
            QFrame.Shape.HLine
        )

        self.header_separator.setFrameShadow(
            QFrame.Shadow.Sunken
        )

        self.body_value = QPlainTextEdit(
            self.details_widget
        )

        self.body_value.setReadOnly(
            True
        )

        self.body_value.setMinimumHeight(
            260
        )

        details_layout.addWidget(
            self.header_widget
        )

        details_layout.addWidget(
            self.header_separator
        )

        details_layout.addWidget(
            self.body_value
        )

        self.add_widget(
            self.placeholder_value
        )

        self.add_widget(
            self.details_widget
        )

        self.refresh_view()

    def refresh_view(
        self,
    ) -> None:
        if not self.view_model.has_message:
            self.placeholder_value.setText(
                self.view_model
                .placeholder_text
            )

            self.placeholder_value.show()
            self.details_widget.hide()

            self._clear_fields()
            return

        self.placeholder_value.hide()
        self.details_widget.show()

        self.sender_value.setText(
            self.view_model.sender
        )

        self.recipients_value.setText(
            self.view_model
            .recipients_text
        )

        self.subject_value.setText(
            self.view_model.subject
        )

        self.size_value.setText(
            self.view_model.size_text
        )

        self.date_value.setText(
            self.view_model
            .internal_date_text
        )

        self.uid_value.setText(
            self.view_model.uid_text
        )

        self.flags_value.setText(
            self.view_model.flags_text
        )

        self.body_value.setPlainText(
            self.view_model.display_body
        )

    def _clear_fields(
        self,
    ) -> None:
        self.sender_value.clear()
        self.recipients_value.clear()
        self.subject_value.clear()
        self.size_value.clear()
        self.date_value.clear()
        self.uid_value.clear()
        self.flags_value.clear()
        self.body_value.clear()

    @staticmethod
    def _make_field_label(
        text: str,
    ) -> QLabel:
        label = QLabel(text)

        label.setObjectName(
            "message_preview_field_label"
        )

        font = label.font()
        font.setBold(True)
        label.setFont(font)

        return label
