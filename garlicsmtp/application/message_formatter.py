from datetime import UTC, datetime

from garlicsmtp.application.message_summary import (
    MessageSummary,
)


class MessageFormatter:

    def __init__(
        self,
        *,
        now_provider=None,
    ) -> None:
        self.now_provider = (
            now_provider
            or self._utc_now
        )

    def format_status(
        self,
        message: MessageSummary,
    ) -> str:
        symbols = []

        if not message.seen:
            symbols.append(
                "●"
            )

        if message.flagged:
            symbols.append(
                "⚑"
            )

        if message.draft:
            symbols.append(
                "✎"
            )

        if message.deleted:
            symbols.append(
                "⌫"
            )

        if not symbols:
            return "✓"

        return " ".join(
            symbols
        )

    def format_sender(
        self,
        message: MessageSummary,
    ) -> str:
        sender = message.sender.strip()

        if not sender:
            return "(Unknown sender)"

        return sender

    def format_subject(
        self,
        message: MessageSummary,
    ) -> str:
        subject = message.subject.strip()

        if not subject:
            return "(No subject)"

        return subject

    def format_date(
        self,
        value: datetime,
    ) -> str:
        local_value = value.astimezone()

        now = self.now_provider().astimezone()

        if local_value.date() == now.date():
            return local_value.strftime(
                "Today %H:%M"
            )

        if (
            local_value.date()
            == now.date().fromordinal(
                now.date().toordinal() - 1
            )
        ):
            return local_value.strftime(
                "Yesterday %H:%M"
            )

        if local_value.year == now.year:
            return local_value.strftime(
                "%d %b %H:%M"
            )

        return local_value.strftime(
            "%Y-%m-%d %H:%M"
        )

    def format_size(
        self,
        size: int,
    ) -> str:
        if size < 0:
            raise ValueError(
                "message size cannot be negative"
            )

        if size < 1024:
            return f"{size} B"

        kilobytes = size / 1024

        if kilobytes < 1024:
            return f"{kilobytes:.1f} KB"

        megabytes = kilobytes / 1024

        if megabytes < 1024:
            return f"{megabytes:.1f} MB"

        gigabytes = megabytes / 1024

        return f"{gigabytes:.1f} GB"

    def build_tooltip(
        self,
        message: MessageSummary,
    ) -> str:
        flags = (
            ", ".join(
                message.flags
            )
            if message.flags
            else "None"
        )

        return (
            f"UID: {message.uid}\n"
            f"From: {self.format_sender(message)}\n"
            f"Subject: {self.format_subject(message)}\n"
            f"Date: {self.format_date(message.internal_date)}\n"
            f"Flags: {flags}\n"
            f"Size: {message.size} bytes"
        )

    @staticmethod
    def _utc_now(
    ) -> datetime:
        return datetime.now(
            UTC
        )
