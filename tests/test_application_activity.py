# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from datetime import datetime, timezone

from garlicsmtp.application import (
    ApplicationActivityFormatter,
    ApplicationEvent,
    ApplicationEventLevel,
    ApplicationEventSource,
)


def make_event(
    *,
    level=ApplicationEventLevel.INFO,
):
    return ApplicationEvent(
        sequence=7,
        timestamp=datetime(
            2026,
            8,
            4,
            8,
            30,
            tzinfo=timezone.utc,
        ),
        source=(
            ApplicationEventSource.TOR
        ),
        level=level,
        message="Tor became ready",
    )


def test_activity_formatter_formats_event():
    entry = (
        ApplicationActivityFormatter()
        .format(
            make_event()
        )
    )

    assert entry.sequence == 7
    assert entry.source_text == "Tor"
    assert entry.level_text == "Info"
    assert entry.status_key == "running"
    assert entry.icon_text == "●"
    assert entry.short_text == (
        "Tor became ready"
    )
    assert entry.details is None


def test_activity_formatter_formats_warning():
    entry = (
        ApplicationActivityFormatter()
        .format(
            make_event(
                level=(
                    ApplicationEventLevel
                    .WARNING
                )
            )
        )
    )

    assert entry.level_text == "Warning"
    assert entry.status_key == "starting"
    assert entry.icon_text == "▲"


def test_activity_formatter_formats_error():
    entry = (
        ApplicationActivityFormatter()
        .format(
            make_event(
                level=(
                    ApplicationEventLevel
                    .ERROR
                )
            )
        )
    )

    assert entry.level_text == "Error"
    assert entry.status_key == "stopped"
    assert entry.icon_text == "■"


def test_activity_formatter_formats_many():
    formatter = (
        ApplicationActivityFormatter()
    )

    entries = formatter.format_many(
        (
            make_event(),
            make_event(
                level=(
                    ApplicationEventLevel
                    .WARNING
                )
            ),
        )
    )

    assert len(entries) == 2
    assert entries[0].level_text == "Info"
    assert entries[1].level_text == (
        "Warning"
    )
