# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.application import (
    ApplicationEventLevel,
    ApplicationEventLog,
    ApplicationEventSource,
    ApplicationViewModel,
)
from garlicsmtp.gui.sections import (
    ActivitySection,
)
from tests.support import (
    make_application_status,
)
from tests.test_gui_main_window import (
    FakeController,
    get_application,
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


def test_activity_section_displays_events():
    get_application()

    controller = (
        build_controller_with_event_log()
    )

    controller.context.event_log.record(
        source=(
            ApplicationEventSource.TOR
        ),
        level=(
            ApplicationEventLevel.INFO
        ),
        message="Tor became ready",
    )

    view_model = ApplicationViewModel(
        controller
    )

    section = ActivitySection(
        view_model=view_model
    )

    section.refresh_view()

    assert (
        section.activity_list.count()
        == 1
    )

    item = section.activity_list.item(
        0
    )

    assert "Tor" in item.text()
    assert "Tor became ready" in item.text()

    assert (
        section.summary_value.text()
        == "1 event"
    )

    assert (
        section.clear_button.isEnabled()
        is True
    )

    section.close()


def test_activity_section_displays_newest_first():
    get_application()

    controller = (
        build_controller_with_event_log()
    )

    controller.context.event_log.record(
        source=(
            ApplicationEventSource.SMTP
        ),
        level=(
            ApplicationEventLevel.INFO
        ),
        message="First event",
    )

    controller.context.event_log.record(
        source=(
            ApplicationEventSource.QUEUE
        ),
        level=(
            ApplicationEventLevel.WARNING
        ),
        message="Second event",
    )

    section = ActivitySection(
        view_model=ApplicationViewModel(
            controller
        )
    )

    section.refresh_view()

    assert "Second event" in (
        section.activity_list
        .item(0)
        .text()
    )

    assert "First event" in (
        section.activity_list
        .item(1)
        .text()
    )

    section.close()


def test_activity_section_clears_events():
    get_application()

    controller = (
        build_controller_with_event_log()
    )

    controller.context.event_log.record(
        source=(
            ApplicationEventSource
            .APPLICATION
        ),
        level=(
            ApplicationEventLevel.INFO
        ),
        message="Application started",
    )

    section = ActivitySection(
        view_model=ApplicationViewModel(
            controller
        )
    )

    section.refresh_view()
    section.clear_activity()

    assert (
        controller.context
        .event_log
        .snapshot()
        == ()
    )

    assert (
        section.activity_list.count()
        == 0
    )

    assert (
        section.summary_value.text()
        == "No events"
    )

    assert (
        section.clear_button.isEnabled()
        is False
    )

    section.close()


def test_activity_section_limits_visible_events():
    get_application()

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
        view_model=ApplicationViewModel(
            controller
        ),
        visible_limit=3,
    )

    section.refresh_view()

    assert (
        section.activity_list.count()
        == 3
    )

    assert "Event 4" in (
        section.activity_list
        .item(0)
        .text()
    )

    section.close()
