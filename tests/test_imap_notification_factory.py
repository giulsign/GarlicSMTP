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