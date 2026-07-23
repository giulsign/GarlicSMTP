from collections import deque
from dataclasses import dataclass, field
from garlicsmtp.imap.notification_sink import (
    IMAPNotificationSink,
)

@dataclass
class IMAPIdleSession(
    IMAPNotificationSink,
    ):
    tag: str | None = None
    notifications: deque[str] = field(
        default_factory=deque,
    )

    @property
    def active(
        self,
    ) -> bool:
        return self.tag is not None

    def should_accept_command(
        self,
    ) -> bool:
        return not self.active

    def enter(
        self,
        tag: str,
    ) -> None:
        self.tag = tag

    def exit(
        self,
    ) -> str | None:
        tag = self.tag
        self.tag = None
        return tag

    def handle_input(
        self,
        line: str,
    ) -> str | None:
        if not self.active:
            return None

        if line.strip().upper() != "DONE":
            return ""

        return self.exit()

    def notify(
        self,
        response: str,
    ) -> None:
        self.notifications.append(
            response,
        )

    def drain_notifications(
        self,
    ) -> tuple[str, ...]:
        notifications = tuple(
            self.notifications
        )

        self.notifications.clear()

        return notifications
    
    def has_notifications(
        self,
    ) -> bool:
        return bool(
            self.notifications
        )
    
    def notify_exists(
        self,
        count: int,
    ) -> None:
        self.notify(
            f"* {count} EXISTS"
        )

    def notify_expunge(
        self,
        sequence: int,
    ) -> None:
        self.notify(
            f"* {sequence} EXPUNGE"
        )

    def notify_response(
        self,
        response: str,
    ) -> None:
        self.notify(
            response
        )

    def notify_mailbox_changed(
        self,
        exists: int,
    ) -> None:
        self.notify_exists(
            exists
        )