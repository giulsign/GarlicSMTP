# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from dataclasses import replace

from garlicsmtp.application.event_hub import (
    ApplicationEventHub,
)
from garlicsmtp.application.tor_monitor_service import (
    TorMonitorService,
)
from garlicsmtp.application.tor_status import (
    TorStatus,
)
from garlicsmtp.application.event_log import (
    ApplicationEventLog,
)
from garlicsmtp.application.event_service import (
    ApplicationEventService,
)


def make_status(
    *,
    authenticated=False,
):
    return TorStatus(
        enabled=True,
        socks_host="127.0.0.1",
        socks_port=9050,
        socks_available=authenticated,
        control_enabled=True,
        control_host="127.0.0.1",
        control_port=9051,
        control_available=authenticated,
        authenticated=authenticated,
        authentication_method=(
            "SAFECOOKIE"
        ),
        version=(
            "0.4.8.12"
            if authenticated
            else None
        ),
        bootstrap_progress=(
            100
            if authenticated
            else None
        ),
        bootstrap_summary=(
            "Done"
            if authenticated
            else None
        ),
        built_circuits=(
            2
            if authenticated
            else 0
        ),
        active_streams=0,
        new_circuits_allowed=False,
        new_circuits_available=False,
        last_error=(
            None
            if authenticated
            else "Not checked"
        ),
        socks_listeners=(),
        control_listeners=(),
        onion_smtp_port=25,
    )


class FakeProvider:

    def __init__(self):
        self.current = make_status()
        self.calls = 0

    def initial_status(self):
        return self.current

    def snapshot(self):
        self.calls += 1
        return self.current


class FakeClock:

    def __init__(self):
        self.value = 0.0

    def __call__(self):
        return self.value


def test_tor_monitor_refreshes_on_first_tick():
    provider = FakeProvider()
    clock = FakeClock()

    service = TorMonitorService(
        provider=provider,
        event_hub=(
            ApplicationEventHub()
        ),
        interval_seconds=10,
        clock=clock,
    )

    service.start()
    service.tick()

    assert provider.calls == 1


def test_tor_monitor_respects_interval():
    provider = FakeProvider()
    clock = FakeClock()

    service = TorMonitorService(
        provider=provider,
        event_hub=(
            ApplicationEventHub()
        ),
        interval_seconds=10,
        clock=clock,
    )

    service.start()
    service.tick()

    clock.value = 9
    service.tick()

    assert provider.calls == 1

    clock.value = 10
    service.tick()

    assert provider.calls == 2


def test_tor_monitor_publishes_when_status_changes():
    provider = FakeProvider()
    hub = ApplicationEventHub()
    events = []

    hub.subscribe(
        lambda: events.append(
            "changed"
        )
    )

    service = TorMonitorService(
        provider=provider,
        event_hub=hub,
    )

    service.start()
    service.tick()

    assert events == []

    provider.current = make_status(
        authenticated=True
    )

    service.refresh()

    assert events == [
        "changed",
    ]


def test_tor_monitor_does_not_publish_unchanged_status():
    provider = FakeProvider()
    hub = ApplicationEventHub()
    events = []

    hub.subscribe(
        lambda: events.append(
            "changed"
        )
    )

    service = TorMonitorService(
        provider=provider,
        event_hub=hub,
    )

    service.start()
    service.refresh()
    service.refresh()

    assert events == []


def test_tor_monitor_does_not_tick_when_stopped():
    provider = FakeProvider()

    service = TorMonitorService(
        provider=provider,
        event_hub=(
            ApplicationEventHub()
        ),
    )

    service.tick()

    assert provider.calls == 0

    service.start()
    service.stop()
    service.tick()

    assert provider.calls == 0


def test_tor_monitor_records_ready_event():
    provider = FakeProvider()
    hub = ApplicationEventHub()
    event_log = ApplicationEventLog()

    event_service = ApplicationEventService(
        event_log=event_log,
        event_hub=hub,
    )

    service = TorMonitorService(
        provider=provider,
        event_hub=hub,
        event_service=event_service,
    )

    service.start()
    service.refresh()

    provider.current = make_status(
        authenticated=True
    )

    service.refresh()

    assert [
        event.message
        for event in event_log.snapshot()
    ] == [
        "Tor became ready",
    ]