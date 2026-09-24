# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.application import (
    ApplicationEventLevel,
    ApplicationEventLog,
    ApplicationEventService,
    ApplicationEventSource,
)
from garlicsmtp.application.event_hub import (
    ApplicationEventHub,
)


def test_event_hub_supports_legacy_listener():
    hub = ApplicationEventHub()
    calls = []

    hub.subscribe(
        lambda: calls.append(
            "changed"
        )
    )

    hub.publish()

    assert calls == [
        "changed",
    ]


def test_event_hub_delivers_event():
    hub = ApplicationEventHub()
    event_log = ApplicationEventLog()
    service = ApplicationEventService(
        event_log=event_log,
        event_hub=hub,
    )

    received = []

    hub.subscribe(
        received.append
    )

    event = service.info(
        ApplicationEventSource.TOR,
        "Tor authenticated",
    )

    assert received == [
        event,
    ]

    assert (
        event.level
        is ApplicationEventLevel.INFO
    )
