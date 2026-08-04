from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QWidget,
)

from garlicsmtp.application import (
    ApplicationActivityEntry,
    ApplicationViewModel,
)
from garlicsmtp.gui.dashboard_widgets import (
    DashboardCard,
)


class ActivitySection(DashboardCard):

    DEFAULT_VISIBLE_LIMIT = 100

    def __init__(
        self,
        *,
        view_model: ApplicationViewModel,
        visible_limit: int = (
            DEFAULT_VISIBLE_LIMIT
        ),
        parent: QWidget | None = None,
    ) -> None:
        if visible_limit <= 0:
            raise ValueError(
                "visible_limit must be "
                "greater than zero"
            )

        super().__init__(
            "Activity",
            parent=parent,
        )

        self.view_model = view_model
        self.visible_limit = visible_limit

        self.summary_value = QLabel(
            "No events"
        )

        self.clear_button = QPushButton(
            "Clear"
        )

        self.clear_button.clicked.connect(
            self.clear_activity
        )

        header = QWidget()

        header_layout = QHBoxLayout(
            header
        )

        header_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        header_layout.addWidget(
            self.summary_value
        )

        header_layout.addStretch()

        header_layout.addWidget(
            self.clear_button
        )

        self.activity_list = QListWidget()

        self.activity_list.setAlternatingRowColors(
            True
        )

        self.activity_list.setMinimumHeight(
            220
        )

        self.activity_list.setSelectionMode(
            QListWidget.SelectionMode
            .NoSelection
        )

        self.add_widget(
            header
        )

        self.add_widget(
            self.activity_list
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

        self.activity_list.clear()

        for entry in entries:
            self.activity_list.addItem(
                self._build_item(
                    entry
                )
            )

        count = len(entries)

        if count == 0:
            self.summary_value.setText(
                "No events"
            )
        elif count == 1:
            self.summary_value.setText(
                "1 event"
            )
        else:
            self.summary_value.setText(
                f"{count} events"
            )

        self.clear_button.setEnabled(
            count > 0
        )

    def clear_activity(
        self,
    ) -> None:
        self.view_model.clear_activity()
        self.refresh_view()

    def _build_item(
        self,
        entry: ApplicationActivityEntry,
    ) -> QListWidgetItem:
        text = (
            f"{entry.timestamp_text}  "
            f"{entry.icon_text}  "
            f"{entry.source_text}  "
            f"{entry.short_text}"
        )

        item = QListWidgetItem(
            text
        )

        item.setData(
            Qt.ItemDataRole.UserRole,
            entry.sequence,
        )

        item.setToolTip(
            self._build_tooltip(
                entry
            )
        )

        self._apply_level_style(
            item,
            entry.status_key,
        )

        return item

    @staticmethod
    def _build_tooltip(
        entry: ApplicationActivityEntry,
    ) -> str:
        parts = [
            entry.timestamp_text,
            entry.source_text,
            entry.level_text,
            entry.short_text,
        ]

        if entry.details:
            parts.append(
                entry.details
            )

        return " — ".join(
            parts
        )

    @staticmethod
    def _apply_level_style(
        item: QListWidgetItem,
        status_key: str,
    ) -> None:
        # I colori usano la palette corrente
        # attraverso il foreground standard.
        # Manteniamo il livello leggibile anche
        # tramite simbolo e testo, non solo colore.
        font = item.font()

        if status_key == "stopped":
            font.setBold(
                True
            )

        elif status_key == "starting":
            font.setItalic(
                True
            )

        item.setFont(
            font
        )
