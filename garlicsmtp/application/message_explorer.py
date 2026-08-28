# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.application.message_summary import (
    MessageSummary,
)
from garlicsmtp.models import MailMessage
from garlicsmtp.storage.entry import (
    MessageEntry,
)
from garlicsmtp.storage.store import (
    MessageStore,
)


class MessageExplorerService:

    def __init__(
        self,
        store: MessageStore,
    ) -> None:
        self.store = store

    def list_messages(
        self,
        mailbox: str,
    ) -> tuple[
        MessageSummary,
        ...,
    ]:
        normalized_mailbox = (
            self._validate_mailbox(
                mailbox
            )
        )

        entries = self.store.list_entries(
            normalized_mailbox
        )

        summaries = tuple(
            self._build_summary(
                entry
            )
            for entry in entries
        )

        return tuple(
            sorted(
                summaries,
                key=lambda item: (
                    item.internal_date,
                    item.uid,
                ),
                reverse=True,
            )
        )

    def get_message(
        self,
        mailbox: str,
        message_id: str,
    ) -> MessageEntry | None:
        normalized_mailbox = (
            self._validate_mailbox(
                mailbox
            )
        )

        normalized_message_id = (
            self._validate_message_id(
                message_id
            )
        )

        return self.store.get_entry(
            normalized_mailbox,
            normalized_message_id,
        )

    def get_summary(
        self,
        mailbox: str,
        message_id: str,
    ) -> MessageSummary | None:
        entry = self.get_message(
            mailbox,
            message_id,
        )

        if entry is None:
            return None

        return self._build_summary(
            entry
        )

    def mark_read(
        self,
        mailbox: str,
        message_id: str,
    ) -> bool:
        normalized_mailbox = (
            self._validate_mailbox(
                mailbox
            )
        )

        normalized_message_id = (
            self._validate_message_id(
                message_id
            )
        )

        return self.store.add_flags(
            normalized_mailbox,
            normalized_message_id,
            {
                "\\Seen",
            },
        )

    def mark_unread(
        self,
        mailbox: str,
        message_id: str,
    ) -> bool:
        normalized_mailbox = (
            self._validate_mailbox(
                mailbox
            )
        )

        normalized_message_id = (
            self._validate_message_id(
                message_id
            )
        )

        return self.store.remove_flags(
            normalized_mailbox,
            normalized_message_id,
            {
                "\\Seen",
            },
        )

    def delete_message(
        self,
        mailbox: str,
        message_id: str,
    ) -> bool:
        normalized_mailbox = (
            self._validate_mailbox(
                mailbox
            )
        )

        normalized_message_id = (
            self._validate_message_id(
                message_id
            )
        )

        return self.store.delete_entry(
            normalized_mailbox,
            normalized_message_id,
        )

    @classmethod
    def _build_summary(
        cls,
        entry: MessageEntry,
    ) -> MessageSummary:
        message = entry.message

        return MessageSummary(
            id=entry.id,
            uid=entry.uid,
            sender=cls._resolve_sender(
                message
            ),
            subject=cls._resolve_subject(
                message
            ),
            internal_date=(
                entry.internal_date
            ),
            size=cls._resolve_size(
                message
            ),
            flags=tuple(
                sorted(
                    entry.flags
                )
            ),
        )

    @staticmethod
    def _resolve_sender(
        message: MailMessage,
    ) -> str:
        header_sender = (
            message.headers.get(
                "From"
            )
        )

        if header_sender:
            return header_sender

        envelope_sender = (
            message.envelope.sender
        )

        if envelope_sender:
            return envelope_sender

        return "(Unknown sender)"

    @staticmethod
    def _resolve_subject(
        message: MailMessage,
    ) -> str:
        subject = message.headers.get(
            "Subject"
        )

        if not subject:
            return "(No subject)"

        return subject

    @staticmethod
    def _resolve_size(
        message: MailMessage,
    ) -> int:
        metadata_size = getattr(
            message.metadata,
            "size",
            0,
        )

        if (
            isinstance(
                metadata_size,
                int,
            )
            and metadata_size > 0
        ):
            return metadata_size

        header_size = sum(
            len(
                f"{key}: {value}\r\n"
                .encode(
                    "utf-8"
                )
            )
            for key, value in (
                message.headers
                .fields
                .items()
            )
        )

        body_size = len(
            message.body.encode(
                "utf-8"
            )
        )

        # Riga vuota tra header e body.
        return (
            header_size
            + 2
            + body_size
        )

    @staticmethod
    def _validate_mailbox(
        mailbox: str,
    ) -> str:
        if not isinstance(
            mailbox,
            str,
        ):
            raise TypeError(
                "mailbox must be text"
            )

        normalized = mailbox.strip()

        if not normalized:
            raise ValueError(
                "mailbox cannot be empty"
            )

        return normalized

    @staticmethod
    def _validate_message_id(
        message_id: str,
    ) -> str:
        if not isinstance(
            message_id,
            str,
        ):
            raise TypeError(
                "message id must be text"
            )

        normalized = (
            message_id.strip()
        )

        if not normalized:
            raise ValueError(
                "message id cannot be empty"
            )

        return normalized
