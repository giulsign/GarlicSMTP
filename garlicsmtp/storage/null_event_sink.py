# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.storage.event_sink import (
    StoreEventSink,
)


class NullStoreEventSink(StoreEventSink):

    def message_added(
        self,
        mailbox: str,
    ) -> None:
        pass

    def message_removed(
        self,
        mailbox: str,
        sequence_number: int,
    ) -> None:
        pass

    def flags_changed(
        self,
        mailbox: str,
    ) -> None:
        pass
