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

        header_widget = QWidget(
            self.details_widget
        )

        header_layout = QFormLayout(
            header_widget
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
            "From",
            self.sender_value,
        )

        header_layout.addRow(
            "To",
            self.recipients_value,
        )

        header_layout.addRow(
            "Subject",
            self.subject_value,
        )

        header_layout.addRow(
            "Size",
            self.size_value,
        )

        header_layout.addRow(
            "Date",
            self.date_value,
        )

        header_layout.addRow(
            "UID",
            self.uid_value,
        )

        header_layout.addRow(
            "Flags",
            self.flags_value,
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
            header_widget
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
            self.view_model.body
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
