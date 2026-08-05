from PySide6.QtCore import (
    Qt,
    Signal,
)
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QWidget,
)

from garlicsmtp.application import (
    ApplicationViewModel,
    MailboxItemViewModel,
)
from garlicsmtp.gui.dashboard_widgets import (
    DashboardCard,
)


class MailboxListSection(DashboardCard):

    mailbox_selected = Signal(
        str
    )

    def __init__(
        self,
        *,
        view_model: ApplicationViewModel,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            "Mailboxes",
            parent=parent,
        )

        self.view_model = view_model

        self.summary_value = QLabel(
            "No mailboxes"
        )

        self.refresh_button = QPushButton(
            "Refresh"
        )

        self.refresh_button.clicked.connect(
            self.refresh_mailboxes
        )

        header = QWidget(
            self
        )

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
            self.refresh_button
        )

        self.mailbox_list = QListWidget(
            self
        )

        self.mailbox_list.setMinimumHeight(
            180
        )

        self.mailbox_list.setAlternatingRowColors(
            True
        )

        self.mailbox_list.currentItemChanged.connect(
            self._on_current_item_changed
        )

        self.add_widget(
            header
        )

        self.add_widget(
            self.mailbox_list
        )

    @property
    def selected_mailbox(
        self,
    ) -> str | None:
        item = self.mailbox_list.currentItem()

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
        selected_mailbox = (
            self.selected_mailbox
        )

        items = (
            self.view_model.mailbox_items
        )

        self.mailbox_list.blockSignals(
            True
        )

        try:
            self.mailbox_list.clear()

            selected_row = None

            for row, mailbox in enumerate(
                items
            ):
                item = self._build_item(
                    mailbox
                )

                self.mailbox_list.addItem(
                    item
                )

                if (
                    mailbox.address
                    == selected_mailbox
                ):
                    selected_row = row

            if selected_row is not None:
                self.mailbox_list.setCurrentRow(
                    selected_row
                )

        finally:
            self.mailbox_list.blockSignals(
                False
            )

        self._update_summary(
            items
        )

    def refresh_mailboxes(
        self,
    ) -> None:
        self.view_model.refresh()
        self.refresh_view()

    def select_mailbox(
        self,
        address: str,
    ) -> bool:
        for row in range(
            self.mailbox_list.count()
        ):
            item = self.mailbox_list.item(
                row
            )

            if (
                item.data(
                    Qt.ItemDataRole.UserRole
                )
                == address
            ):
                self.mailbox_list.setCurrentRow(
                    row
                )

                return True

        return False

    @staticmethod
    def _build_item(
        mailbox: MailboxItemViewModel,
    ) -> QListWidgetItem:
        item = QListWidgetItem(
            mailbox.display_text
        )

        item.setData(
            Qt.ItemDataRole.UserRole,
            mailbox.address,
        )

        item.setToolTip(
            (
                f"{mailbox.address}\n"
                f"{mailbox.message_count_text}"
            )
        )

        return item

    def _update_summary(
        self,
        items: tuple[
            MailboxItemViewModel,
            ...
        ],
    ) -> None:
        mailbox_count = len(
            items
        )

        message_count = sum(
            item.message_count
            for item in items
        )

        if mailbox_count == 0:
            self.summary_value.setText(
                "No mailboxes"
            )
            return

        mailbox_label = (
            "mailbox"
            if mailbox_count == 1
            else "mailboxes"
        )

        message_label = (
            "message"
            if message_count == 1
            else "messages"
        )

        self.summary_value.setText(
            (
                f"{mailbox_count} "
                f"{mailbox_label}, "
                f"{message_count} "
                f"{message_label}"
            )
        )

    def _on_current_item_changed(
        self,
        current,
        previous,
    ) -> None:
        del previous

        if current is None:
            return

        mailbox = current.data(
            Qt.ItemDataRole.UserRole
        )

        if isinstance(
            mailbox,
            str,
        ):
            self.mailbox_selected.emit(
                mailbox
            )
