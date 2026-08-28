# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class StatusBadge(QLabel):

    def __init__(
        self,
        text: str = "",
        *,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            text,
            parent,
        )

        self.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.setMinimumWidth(
            100
        )

        self.setContentsMargins(
            10,
            4,
            10,
            4,
        )

        self.set_status(
            text=text,
            status_key="stopped",
        )

    def set_status(
        self,
        *,
        text: str,
        status_key: str,
    ) -> None:
        self.setText(
            text
        )

        styles = {
            "running": (
                "background-color: #1f7a45;"
                "color: white;"
            ),
            "starting": (
                "background-color: #9a6a00;"
                "color: white;"
            ),
            "stopping": (
                "background-color: #9a6a00;"
                "color: white;"
            ),
            "stopped": (
                "background-color: #8b2d2d;"
                "color: white;"
            ),
            "disabled": (
                "background-color: #555555;"
                "color: white;"
            ),
        }

        style = styles.get(
            status_key,
            styles["stopped"],
        )

        self.setStyleSheet(
            f"""
            QLabel {{
                {style}
                border-radius: 10px;
                font-weight: 600;
            }}
            """
        )


class MetricValue(QWidget):

    def __init__(
        self,
        title: str,
        *,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            parent
        )

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        layout.setSpacing(
            2
        )

        self.title_label = QLabel(
            title
        )

        self.title_label.setStyleSheet(
            """
            QLabel {
                color: #777777;
                font-size: 11px;
            }
            """
        )

        self.value_label = QLabel(
            "—"
        )

        self.value_label.setTextInteractionFlags(
            Qt.TextInteractionFlag
            .TextSelectableByMouse
        )

        self.value_label.setStyleSheet(
            """
            QLabel {
                font-size: 15px;
                font-weight: 600;
            }
            """
        )

        layout.addWidget(
            self.title_label
        )

        layout.addWidget(
            self.value_label
        )

    def setText(
        self,
        text: str,
    ) -> None:
        self.value_label.setText(
            text
        )

    def text(
        self,
    ) -> str:
        return self.value_label.text()


class DashboardCard(QFrame):

    def __init__(
        self,
        title: str,
        *,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            parent
        )

        self.setFrameShape(
            QFrame.Shape.StyledPanel
        )

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        self.setStyleSheet(
            """
            DashboardCard {
                border: 1px solid #444444;
                border-radius: 8px;
            }
            """
        )

        self.root_layout = QVBoxLayout(
            self
        )

        self.root_layout.setContentsMargins(
            16,
            14,
            16,
            14,
        )

        self.root_layout.setSpacing(
            10
        )

        title_label = QLabel(
            title
        )

        title_label.setStyleSheet(
            """
            QLabel {
                font-size: 16px;
                font-weight: 700;
            }
            """
        )

        self.root_layout.addWidget(
            title_label
        )

        self.content_layout = QVBoxLayout()

        self.content_layout.setSpacing(
            8
        )

        self.root_layout.addLayout(
            self.content_layout
        )

    def add_widget(
        self,
        widget: QWidget,
    ) -> None:
        self.content_layout.addWidget(
            widget
        )

    def add_row(
        self,
        label: str,
        widget: QWidget,
    ) -> None:
        row = QWidget()

        layout = QHBoxLayout(
            row
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        name_label = QLabel(
            label
        )

        name_label.setMinimumWidth(
            140
        )

        layout.addWidget(
            name_label
        )

        layout.addStretch()

        layout.addWidget(
            widget
        )

        self.add_widget(
            row
        )
