from garlicsmtp.imap.null_notification_sink import (
    NullIMAPNotificationSink,
)


def test_null_notification_sink_discards_notifications():
    sink = NullIMAPNotificationSink()

    sink.notify_mailbox_changed(5)
    sink.notify_expunge(2)

    assert sink.has_notifications() is False
    assert sink.drain_notifications() == ()