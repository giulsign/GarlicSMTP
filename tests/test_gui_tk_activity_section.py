# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import tkinter as tk

import pytest

from garlicsmtp.application import (
    ApplicationEventLevel,
    ApplicationEventLog,
    ApplicationEventSource,
    ApplicationViewModel,
)
from garlicsmtp.gui.tk_activity_section import (
    ActivitySection,
)
from tests.support import (
    FakeController,
    make_application_status,
)


def build_controller_with_event_log():
    controller = FakeController()

    controller.current_status = (
        make_application_status()
    )

    controller.context = type(
        "Context",
        (),
        {
            "event_log": (
                ApplicationEventLog()
            )
        },
    )()

    return controller


def test_activity_section_displays_events_newest_first():
    root = tk.Tk()
    root.withdraw()

    try:
        controller = (
            build_controller_with_event_log()
        )

        controller.context.event_log.record(
            source=ApplicationEventSource.SMTP,
            level=ApplicationEventLevel.INFO,
            message="First event",
        )
        controller.context.event_log.record(
            source=ApplicationEventSource.QUEUE,
            level=ApplicationEventLevel.WARNING,
            message="Second event",
        )

        section = ActivitySection(
            root,
            view_model=ApplicationViewModel(
                controller
            ),
        )

        section.refresh_view()

        assert (
            section.activity_list.size()
            == 2
        )
        assert "Second event" in (
            section.activity_list.get(0)
        )
        assert "First event" in (
            section.activity_list.get(1)
        )
        assert (
            section.summary_value.cget("text")
            == "2 events"
        )
        assert section.clear_button.instate(
            ["!disabled"]
        )

    finally:
        root.destroy()


def test_activity_section_limits_visible_events():
    root = tk.Tk()
    root.withdraw()

    try:
        controller = (
            build_controller_with_event_log()
        )

        for index in range(5):
            controller.context.event_log.record(
                source=(
                    ApplicationEventSource.QUEUE
                ),
                level=(
                    ApplicationEventLevel.INFO
                ),
                message=f"Event {index}",
            )

        section = ActivitySection(
            root,
            view_model=ApplicationViewModel(
                controller
            ),
            visible_limit=3,
        )

        section.refresh_view()

        assert (
            section.activity_list.size()
            == 3
        )
        assert "Event 4" in (
            section.activity_list.get(0)
        )
        assert (
            section.summary_value.cget("text")
            == "3 events"
        )

    finally:
        root.destroy()


def test_activity_section_rejects_invalid_visible_limit():
    root = tk.Tk()
    root.withdraw()

    try:
        with pytest.raises(
            ValueError,
            match="visible_limit",
        ):
            ActivitySection(
                root,
                view_model=ApplicationViewModel(
                    FakeController()
                ),
                visible_limit=0,
            )

    finally:
        root.destroy()


def test_activity_section_clears_events():
    root = tk.Tk()
    root.withdraw()

    try:
        controller = (
            build_controller_with_event_log()
        )

        controller.context.event_log.record(
            source=(
                ApplicationEventSource.APPLICATION
            ),
            level=(
                ApplicationEventLevel.INFO
            ),
            message="Application started",
        )

        section = ActivitySection(
            root,
            view_model=ApplicationViewModel(
                controller
            ),
        )

        section.refresh_view()

        assert (
            section.activity_list.size()
            == 1
        )
        assert section.clear_button.instate(
            ["!disabled"]
        )

        section.clear_button.invoke()

        assert (
            controller.context
            .event_log
            .snapshot()
            == ()
        )
        assert (
            section.activity_list.size()
            == 0
        )
        assert (
            section.summary_value.cget("text")
            == "No events"
        )
        assert section.clear_button.instate(
            ["disabled"]
        )

    finally:
        root.destroy()