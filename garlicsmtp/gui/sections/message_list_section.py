from PySide6.QtCore import (
    Qt,
    Signal,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QMessageBox,
    QWidget,
)

from garlicsmtp.application import (
    MessageListViewModel,
    MessageSummary,
)
from garlicsmtp.gui.dashboard_widgets import (
    DashboardCard,
)
from garlicsmtp.application import (
    MessageFormatter,
    MessageListViewModel,
    MessageSummary,
)


class MessageListSection(DashboardCard):

    message_selected = Signal(
        str
    )

    message_deleted = Signal(
        str
    )

    COLUMN_STATUS = 0
    COLUMN_UID = 1
    COLUMN_SENDER = 2
    COLUMN_SUBJECT = 3
    COLUMN_DATE = 4
    COLUMN_SIZE = 5

    def __init__(
        self,
        *,
        view_model: MessageListViewModel,
        formatter: MessageFormatter | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            "Messages",
            parent=parent,
        )

        self.refresh_button = QPushButton(
            "Refresh",
            self,
        )

        self.refresh_button.clicked.connect(
            self._refresh_messages
        )

        self.mark_read_button = QPushButton(
            "Mark read",
            self,
        )

        self.mark_read_button.clicked.connect(
            self._mark_selected_read
        )

        self.mark_unread_button = QPushButton(
            "Mark unread",
            self,
        )

        self.mark_unread_button.clicked.connect(
            self._mark_selected_unread
        )

        self.delete_button = QPushButton(
            "Delete",
            self,
        )

        self.delete_button.clicked.connect(
            self._delete_selected_message
        )

        self.formatter = (
            formatter
            or MessageFormatter()
        )

        self.view_model = view_model

        self.table = QTableWidget(
            self
        )

        self.table.setColumnCount(
            6
        )

        self.table.setHorizontalHeaderLabels(
            [
                "Status",
                "UID",
                "From",
                "Subject",
                "Date",
                "Size",
            ]
        )

        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior
            .SelectRows
        )

        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode
            .SingleSelection
        )

        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger
            .NoEditTriggers
        )

        self.table.setAlternatingRowColors(
            True
        )

        self.table.setSortingEnabled(
            False
        )

        self.table.verticalHeader().setVisible(
            False
        )

        header = self.table.horizontalHeader()

        header.setSectionResizeMode(
            self.COLUMN_STATUS,
            QHeaderView.ResizeMode
            .ResizeToContents,
        )

        header.setSectionResizeMode(
            self.COLUMN_UID,
            QHeaderView.ResizeMode
            .ResizeToContents,
        )

        header.setSectionResizeMode(
            self.COLUMN_SENDER,
            QHeaderView.ResizeMode
            .Interactive,
        )

        header.setSectionResizeMode(
            self.COLUMN_SUBJECT,
            QHeaderView.ResizeMode
            .Stretch,
        )

        header.setSectionResizeMode(
            self.COLUMN_DATE,
            QHeaderView.ResizeMode
            .ResizeToContents,
        )

        header.setSectionResizeMode(
            self.COLUMN_SIZE,
            QHeaderView.ResizeMode
            .ResizeToContents,
        )

        self.table.setMinimumHeight(
            260
        )

        self.table.currentCellChanged.connect(
            self._on_current_cell_changed
        )

        self.add_widget(
            self.refresh_button
        )

        self.add_widget(
            self.mark_read_button
        )

        self.add_widget(
            self.mark_unread_button
        )

        self.add_widget(
            self.delete_button
        )

        self.add_widget(
            self.table
        )

    @property
    def selected_message_id(
        self,
    ) -> str | None:
        row = self.table.currentRow()

        if row < 0:
            return None

        item = self.table.item(
            row,
            self.COLUMN_UID,
        )

        if item is None:
            return None

        value = item.data(
            Qt.ItemDataRole.UserRole
        )

        if not isinstance(
            value,
            str,
        ):
            return None

        return value

    def refresh_view(
        self,
    ) -> None:
        selected_message_id = (
            self.view_model
            .selected_message_id
        )

        messages = (
            self.view_model.messages
        )

        self.table.blockSignals(
            True
        )

        try:
            self.table.setRowCount(
                len(messages)
            )

            selected_row = None

            for row, message in enumerate(
                messages
            ):
                self._populate_row(
                    row,
                    message,
                )

                if (
                    message.id
                    == selected_message_id
                ):
                    selected_row = row

            if selected_row is not None:
                self.table.selectRow(
                    selected_row
                )
            else:
                self.table.clearSelection()
                self.table.setCurrentCell(
                    -1,
                    -1,
                )

        finally:
            self.table.blockSignals(
                False
            )

    def select_message(
        self,
        message_id: str,
    ) -> bool:
        for row in range(
            self.table.rowCount()
        ):
            item = self.table.item(
                row,    
                self.COLUMN_UID,
            )

            if item is None:
                continue

            if (
                item.data(
                    Qt.ItemDataRole.UserRole
                )
                != message_id
            ):
                continue

            if (
                self.table.currentRow()
                == row
            ):
                return True

            self.table.setCurrentCell(
                row,
                self.COLUMN_SUBJECT,
            )

            return True

        return False

    def clear(
        self,
    ) -> None:
        self.table.setRowCount(
            0
        )

        self.table.clearSelection()

    def _populate_row(
        self,
        row: int,
        message: MessageSummary,
    ) -> None:
        status_item = QTableWidgetItem(
            self.formatter.format_status(
                message
            )
        )

        status_item.setTextAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        uid_item = QTableWidgetItem(
            str(
                message.uid
            )
        )

        uid_item.setData(
            Qt.ItemDataRole.UserRole,
            message.id,
        )

        uid_item.setTextAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignVCenter
        )

        sender_item = QTableWidgetItem(
            self.formatter.format_sender(
                message
            )
        )

        subject_item = QTableWidgetItem(
            self.formatter.format_subject(
                message
            )
        )

        date_item = QTableWidgetItem(
            self.formatter.format_date(
                message.internal_date
            )
        )

        size_item = QTableWidgetItem(
            self.formatter.format_size(
                message.size
            )
        )

        size_item.setTextAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignVCenter
        )

        tooltip = self.formatter.build_tooltip(
                    message
                )

        for item in (
            status_item,
            uid_item,
            sender_item,
            subject_item,
            date_item,
            size_item,
        ):
            item.setToolTip(
                tooltip
            )

        if not message.seen:
            font = subject_item.font()
            font.setBold(
                True
            )

            sender_item.setFont(
                font
            )

            subject_item.setFont(
                font
            )

        self.table.setItem(
            row,
            self.COLUMN_STATUS,
            status_item,
        )

        self.table.setItem(
            row,
            self.COLUMN_UID,
            uid_item,
        )

        self.table.setItem(
            row,
            self.COLUMN_SENDER,
            sender_item,
        )

        self.table.setItem(
            row,
            self.COLUMN_SUBJECT,
            subject_item,
        )

        self.table.setItem(
            row,
            self.COLUMN_DATE,
            date_item,
        )

        self.table.setItem(
            row,
            self.COLUMN_SIZE,
            size_item,
        )

    def _on_current_cell_changed(
        self,
        current_row: int,
        current_column: int,
        previous_row: int,
        previous_column: int,
    ) -> None:
        del current_column
        del previous_row
        del previous_column

        if current_row < 0:
            self.view_model.select_message(
                None
            )

            return

        item = self.table.item(
            current_row,
            self.COLUMN_UID,
        )

        if item is None:
            return

        message_id = item.data(
            Qt.ItemDataRole.UserRole
        )

        if not isinstance(
            message_id,
            str,
        ):
            return

        if self.view_model.select_message(
            message_id
        ):
            self.message_selected.emit(
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

        answer = QMessageBox.question(
            self,
            "Delete message",
            "Delete the selected message?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        if self.view_model.delete_selected():
            self.refresh_view()

            self.message_deleted.emit(
                message_id
            )

    
