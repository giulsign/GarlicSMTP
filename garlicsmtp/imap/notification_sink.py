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