# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from collections.abc import Callable

from garlicsmtp.application.message_explorer import (
    MessageExplorerService,
)
from html.parser import HTMLParser


MessagePreviewListener = Callable[
    [],
    None,
]


class _HTMLTextExtractor(HTMLParser):

    def __init__(
        self,
    ) -> None:
        super().__init__()

        self.parts: list[str] = []

    def handle_data(
        self,
        data: str,
    ) -> None:
        self.parts.append(
            data
        )

    def text(
        self,
    ) -> str:
        return "".join(
            self.parts
        ).strip()


class MessagePreviewViewModel:

    def __init__(
        self,
        explorer: MessageExplorerService,
    ) -> None:
        self.explorer = explorer

        self._mailbox: str | None = None
        self._message_id: str | None = None
        self._entry = None

        self._listeners: list[
            MessagePreviewListener
        ] = []

    @property
    def mailbox(
        self,
    ) -> str | None:
        return self._mailbox

    @property
    def message_id(
        self,
    ) -> str | None:
        return self._message_id

    @property
    def has_message(
        self,
    ) -> bool:
        return self._entry is not None

    @property
    def sender(
        self,
    ) -> str:
        if self._entry is None:
            return ""

        message = self._entry.message

        header_sender = (
            message.headers.get(
                "From"
            )
        )

        if header_sender:
            return header_sender

        return (
            message.envelope.sender
            or "(Unknown sender)"
        )

    @property
    def recipients(
        self,
    ) -> tuple[str, ...]:
        if self._entry is None:
            return ()

        return tuple(
            self._entry
            .message
            .envelope
            .recipients
        )

    @property
    def recipients_text(
        self,
    ) -> str:
        if not self.recipients:
            return ""

        return ", ".join(
            self.recipients
        )

    @property
    def subject(
        self,
    ) -> str:
        if self._entry is None:
            return ""

        subject = (
            self._entry
            .message
            .headers
            .get(
                "Subject"
            )
        )

        return (
            subject
            or "(No subject)"
        )

    @property
    def internal_date(
        self,
    ):
        if self._entry is None:
            return None

        return self._entry.internal_date

    @property
    def internal_date_text(
        self,
    ) -> str:
        if self.internal_date is None:
            return ""

        return (
            self.internal_date
            .astimezone()
            .strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )

    @property
    def uid(
        self,
    ) -> int | None:
        if self._entry is None:
            return None

        return self._entry.uid

    @property
    def uid_text(
        self,
    ) -> str:
        if self.uid is None:
            return ""

        return str(
            self.uid
        )

    @property
    def size(
        self,
    ) -> int | None:
        if self._entry is None:
            return None

        return self._entry.message.metadata.size

    @property
    def size_text(
        self,
    ) -> str:
        if self.size is None:
            return ""

        return self._format_size(
            self.size
        )

    @property
    def flags(
        self,
    ) -> tuple[str, ...]:
        if self._entry is None:
            return ()

        return tuple(
            sorted(
                self._entry.flags
            )
        )

    @property
    def flags_text(
        self,
    ) -> str:
        if not self.flags:
            return "None"

        return ", ".join(
            self.flags
        )

    @property
    def body(
        self,
    ) -> str:
        if self._entry is None:
            return ""

        return (
            self._entry
            .message
            .body
        )

    @property
    def content_type(
        self,
    ) -> str:
        if self._entry is None:
            return ""

        content_type = (
            self._entry
            .message
            .headers
            .get(
                "Content-Type",
                ""
            )
        )

        if not content_type:
            return ""

        return (
            content_type
            .split(
                ";",
                1,
            )[0]
            .strip()
            .lower()
        )


    @property
    def is_html(
        self,
    ) -> bool:
        return (
            self.content_type
            == "text/html"
        )

    @property
    def placeholder_text(
        self,
    ) -> str:
        if self._mailbox is None:
            return "Select a mailbox"

        if self._message_id is None:
            return "Select a message"

        if self._entry is None:
            return "Message unavailable"

        return ""

    def subscribe(
        self,
        listener: MessagePreviewListener,
    ) -> None:
        if listener not in self._listeners:
            self._listeners.append(
                listener
            )

    def unsubscribe(
        self,
        listener: MessagePreviewListener,
    ) -> None:
        if listener in self._listeners:
            self._listeners.remove(
                listener
            )

    def select_message(
        self,
        *,
        mailbox: str | None,
        message_id: str | None,
    ) -> None:
        normalized_mailbox = (
            self._normalize_text(
                mailbox
            )
        )

        normalized_message_id = (
            self._normalize_text(
                message_id
            )
        )

        changed = (
            normalized_mailbox
            != self._mailbox
            or normalized_message_id
            != self._message_id
        )

        self._mailbox = (
            normalized_mailbox
        )

        self._message_id = (
            normalized_message_id
        )

        self._load()

        if changed:
            self._notify()

    def refresh(
        self,
    ) -> None:
        previous = self._entry

        self._load()

        if self._entry != previous:
            self._notify()

    def clear(
        self,
    ) -> None:
        changed = (
            self._mailbox is not None
            or self._message_id is not None
            or self._entry is not None
        )

        self._mailbox = None
        self._message_id = None
        self._entry = None

        if changed:
            self._notify()

    def _load(
        self,
    ) -> None:
        if (
            self._mailbox is None
            or self._message_id is None
        ):
            self._entry = None
            return

        self._entry = (
            self.explorer.get_message(
                self._mailbox,
                self._message_id,
            )
        )

    def _notify(
        self,
    ) -> None:
        for listener in tuple(
            self._listeners
        ):
            listener()
    
    @staticmethod
    def _format_size(
        size: int,
    ) -> str:
        if size < 1024:
            return f"{size} B"

        if size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"

        if size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"

        return f"{size / (1024 * 1024 * 1024):.1f} GB"

    @staticmethod
    def _normalize_text(
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                "value must be text"
            )

        normalized = value.strip()

        if not normalized:
            return None

        return normalized

    @property
    def display_body(
        self,
    ) -> str:
        if not self.body:
            return ""

        if not self.is_html:
            return self.body

        parser = _HTMLTextExtractor()

        parser.feed(
            self.body
        )

        return parser.text()
