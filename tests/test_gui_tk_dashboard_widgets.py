# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import tkinter as tk
from tkinter import ttk

from garlicsmtp.gui.tk_dashboard_widgets import (
    DashboardCard,
)


def test_dashboard_card_builds_titled_content_area():
    root = tk.Tk()
    root.withdraw()

    try:
        card = DashboardCard(
            root,
            title="Application",
        )

        assert isinstance(card, ttk.Frame)
        assert card.title == "Application"

        assert isinstance(
            card.title_label,
            ttk.Label,
        )

        assert (
            card.title_label.cget("text")
            == "Application"
        )

        assert isinstance(
            card.content,
            ttk.Frame,
        )

        assert (
            card.cget("style")
            == "Garlic.Card.TFrame"
        )

        assert (
            card.title_label.cget("style")
            == "Garlic.CardTitle.TLabel"
        )

    finally:
        root.destroy()



def test_selectable_value_is_read_only_and_selectable():
    root = tk.Tk()
    root.withdraw()

    try:
        from garlicsmtp.gui.tk_dashboard_widgets import (
            SelectableValue,
        )

        value = SelectableValue(
            root,
            text="garlicsmtp.local",
        )

        assert isinstance(value, ttk.Entry)
        assert value.get() == "garlicsmtp.local"
        assert value.instate(["readonly"])
        assert not value.instate(["disabled"])
        assert value.cget("style") == (
            "Garlic.Readonly.TEntry"
        )

        value.set_text("test.onion")

        assert value.get() == "test.onion"

    finally:
        root.destroy()


def test_status_badge_updates_text_and_status():
    root = tk.Tk()
    root.withdraw()

    try:
        from garlicsmtp.gui.tk_dashboard_widgets import (
            StatusBadge,
        )

        badge = StatusBadge(
            root,
        )

        badge.set_status(
            text="Running",
            status_key="running",
        )

        assert badge.get() == "Running"
        assert badge.status_key == "running"
        assert badge.instate(["readonly"])
        assert not badge.instate(["disabled"])

        badge.set_status(
            text="Stopped",
            status_key="stopped",
        )

        assert badge.get() == "Stopped"
        assert badge.status_key == "stopped"

    finally:
        root.destroy()


def test_metric_value_displays_label_and_value():
    root = tk.Tk()
    root.withdraw()

    try:
        from garlicsmtp.gui.tk_dashboard_widgets import (
            MetricValue,
        )

        metric = MetricValue(
            root,
            label="Queue",
        )

        assert metric.label.cget("text") == "Queue"
        assert metric.value.get() == ""

        metric.set_text(
            "7 messages queued"
        )

        assert (
            metric.value.get()
            == "7 messages queued"
        )
        assert metric.value.instate(
            ["readonly"]
        )

    finally:
        root.destroy()