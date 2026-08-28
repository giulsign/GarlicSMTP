# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.imap.notification_sink import (
    IMAPNotificationSink,
)
from garlicsmtp.imap.null_notification_sink import (
    NullIMAPNotificationSink,
)


def notification_sink(
    idle: IMAPNotificationSink | None,
) -> IMAPNotificationSink:
    if idle is None:
        return NullIMAPNotificationSink()

    return idle