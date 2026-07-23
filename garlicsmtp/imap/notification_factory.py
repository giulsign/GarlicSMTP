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