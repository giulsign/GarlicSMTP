# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.imap.idle import (
    IMAPIdleSession,
)
from garlicsmtp.imap.notification_factory import (
    notification_sink,
)
from garlicsmtp.imap.null_notification_sink import (
    NullIMAPNotificationSink,
)


def test_notification_sink_returns_idle_session():
    idle = IMAPIdleSession()

    assert notification_sink(idle) is idle


def test_notification_sink_returns_null_sink():
    sink = notification_sink(None)

    assert isinstance(
        sink,
        NullIMAPNotificationSink,
    )