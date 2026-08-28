# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.imap.notification_sink import (
    IMAPNotificationSink,
)
from garlicsmtp.storage.event_sink import (
    StoreEventSink,
)


class IMAPStoreEventAdapter(
    StoreEventSink
):

    def __init__(
        self,
        *,
        notification_sink: IMAPNotificationSink,
        selected_mailbox: callable,
        mailbox_count: callable,
    ) -> None:
        self.notification_sink = (
            notification_sink
        )
        self.selected_mailbox = (
            selected_mailbox
        )
        self.mailbox_count = (
            mailbox_count
        )

    def message_added(
        self,
        mailbox: str,
    ) -> None:
        if mailbox != self.selected_mailbox():
            return

        self.notification_sink.notify_mailbox_changed(
            self.mailbox_count(
                mailbox
            )
        )

    def message_removed(
        self,
        mailbox: str,
        sequence_number: int,
    ) -> None:
        if mailbox != self.selected_mailbox():
            return

        self.notification_sink.notify_expunge(
            sequence_number
        )

    def flags_changed(
        self,
        mailbox: str,
    ) -> None:
        return
