# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from typing import Protocol


class IMAPNotificationSink(Protocol):
    def notify_mailbox_changed(
        self,
        exists: int,
    ) -> None: ...

    def notify_expunge(
        self,
        sequence: int,
    ) -> None: ...

    def has_notifications(
        self,
    ) -> bool: ...


    def drain_notifications(
        self,
    ) -> tuple[str, ...]: ...