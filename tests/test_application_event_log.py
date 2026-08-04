from datetime import datetime, timezone

import pytest

from garlicsmtp.application import (
    ApplicationEventLevel,
    ApplicationEventLog,
    ApplicationEventSource,
)


def fixed_clock():
    return datetime(
        2026,
        8,
        4,
        8,
        30,
        tzinfo=timezone.utc,
    )


def test_event_log_records_event():
    event_log = ApplicationEventLog(
        clock=fixed_clock
    )

    event = event_log.record(
        source=(
            ApplicationEventSource.SMTP
        ),
        level=(
            ApplicationEventLevel.INFO
        ),
        message="SMTP server started",
    )

    assert event.sequence == 1
    assert event.timestamp == fixed_clock()
    assert event.message == (
        "SMTP server started"
    )

    assert event_log.snapshot() == (
        event,
    )


def test_event_log_limits_capacity():
    event_log = ApplicationEventLog(
        capacity=2,
        clock=fixed_clock,
    )

    first = event_log.record(
        source=(
            ApplicationEventSource
            .APPLICATION
        ),
        level=(
            ApplicationEventLevel.INFO
        ),
        message="first",
    )

    second = event_log.record(
        source=(
            ApplicationEventSource
            .APPLICATION
        ),
        level=(
            ApplicationEventLevel.INFO
        ),
        message="second",
    )

    third = event_log.record(
        source=(
            ApplicationEventSource
            .APPLICATION
        ),
        level=(
            ApplicationEventLevel.INFO
        ),
        message="third",
    )

    assert event_log.snapshot() == (
        second,
        third,
    )

    assert first not in event_log.snapshot()


def test_event_log_returns_newest_first():
    event_log = ApplicationEventLog(
        clock=fixed_clock
    )

    first = event_log.record(
        source=(
            ApplicationEventSource.QUEUE
        ),
        level=(
            ApplicationEventLevel.INFO
        ),
        message="first",
    )

    second = event_log.record(
        source=(
            ApplicationEventSource.QUEUE
        ),
        level=(
            ApplicationEventLevel.INFO
        ),
        message="second",
    )

    assert event_log.snapshot(
        newest_first=True
    ) == (
        second,
        first,
    )


def test_event_log_normalizes_message():
    event_log = ApplicationEventLog(
        clock=fixed_clock
    )

    event = event_log.record(
        source=(
            ApplicationEventSource.TOR
        ),
        level=(
            ApplicationEventLevel.WARNING
        ),
        message="  Tor   status\n unavailable ",
    )

    assert event.message == (
        "Tor status unavailable"
    )


def test_event_log_rejects_empty_message():
    event_log = ApplicationEventLog()

    with pytest.raises(
        ValueError
    ):
        event_log.record(
            source=(
                ApplicationEventSource.IMAP
            ),
            level=(
                ApplicationEventLevel.INFO
            ),
            message="   ",
        )


def test_event_log_clears_events():
    event_log = ApplicationEventLog()

    event_log.record(
        source=(
            ApplicationEventSource.STORE
        ),
        level=(
            ApplicationEventLevel.INFO
        ),
        message="Message stored",
    )

    event_log.clear()

    assert event_log.snapshot() == ()
    assert len(event_log) == 0
