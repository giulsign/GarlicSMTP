from garlicsmtp.imap.notification_sink import (
    IMAPNotificationSink,
)


class NullIMAPNotificationSink(
    IMAPNotificationSink,
):
    def notify_mailbox_changed(
        self,
        exists: int,
    ) -> None:
        pass

    def notify_expunge(
        self,
        sequence: int,
    ) -> None:
        pass

    def has_notifications(
        self,
    ) -> bool:
        return False

    def drain_notifications(
        self,
    ) -> tuple[str, ...]:
        return ()