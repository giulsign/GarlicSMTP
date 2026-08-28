# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from dataclasses import dataclass
from typing import Callable

from garlicsmtp.imap.literal import (
    IMAPLiteralResponse,
)
from garlicsmtp.imap.reply import IMAPReply
from garlicsmtp.imap.response import IMAPResponse
from garlicsmtp.storage.entry import MessageEntry
from garlicsmtp.storage.serializer import (
    MessageSerializer,
)
from email.utils import getaddresses


class IMAPFetchError(ValueError):
    pass


@dataclass(slots=True)
class IMAPFetchRenderer:

    entry: MessageEntry
    sequence_number: int
    mark_seen: bool = False

    SEEN_ITEMS = {
        "BODY[]",
        "BODY[TEXT]",
        "RFC822",
        "RFC822.TEXT",
    }

    ITEM_ORDER = (
        "UID",
        "FLAGS",
        "INTERNALDATE",
        "ENVELOPE",
        "BODY",
        "RFC822.SIZE",
        "RFC822.HEADER",
        "RFC822.TEXT",
        "RFC822",
        "BODY.PEEK[]",
        "BODY.PEEK[HEADER]",
        "BODY.PEEK[TEXT]",
        "BODY[HEADER]",
        "BODY[TEXT]",
        "BODY[]",
    )

    def render(
        self,
        requested_items: set[str],
    ) -> IMAPResponse:
        handlers = self._build_handlers()

        header_fields_item = next(
            (
                item
                for item in requested_items
                if (
                    item.startswith(
                        "BODY[HEADER.FIELDS ("
                    )
                    or item.startswith(
                        "BODY.PEEK[HEADER.FIELDS ("
                    )
                    or item.startswith(
                        "BODY[HEADER.FIELDS.NOT ("
                    )
                    or item.startswith(
                        "BODY.PEEK[HEADER.FIELDS.NOT ("
                    )
                )
                and item.endswith(")]")
            ),
            None,
        )

        partial_body_item = next(
            (
                item
                for item in requested_items
                if (
                    (
                        item.startswith(
                            "BODY[]<"
                        )
                        or item.startswith(
                            "BODY.PEEK[]<"
                        )
                        or item.startswith(
                            "BODY[TEXT]<"
                        )
                        or item.startswith(
                            "BODY.PEEK[TEXT]<"
                        )
                    )
                    and item.endswith(">")
                )
            ),
            None,
        )

        supported_items = set(
            handlers.keys()
        )

        if header_fields_item is not None:
            supported_items.add(
                header_fields_item
            )

        if partial_body_item is not None:
            supported_items.add(
                partial_body_item
            )

        unsupported = (
            requested_items
            - supported_items
        )

        if unsupported:
            item = sorted(unsupported)[0]

            raise IMAPFetchError(
                f"Unsupported FETCH item {item}"
            )

        self.mark_seen = bool(
            requested_items
            & self.SEEN_ITEMS
        )

        if (
            partial_body_item is not None
            and (
                partial_body_item.startswith(
                    "BODY[]<"
                )
                or partial_body_item.startswith(
                    "BODY[TEXT]<"
                )
            )
        ):
            self.mark_seen = True

        rendered_values = []
        literal_item = None
        literal_content = None

        for item in self.ITEM_ORDER:
            if item not in requested_items:
                continue

            handler = handlers[item]
            result = handler()

            if isinstance(result, bytes):
                literal_item = item
                literal_content = result
            else:
                rendered_values.append(result)

        if header_fields_item is not None:
            literal_item = header_fields_item
            literal_content = (
                self._render_body_header_fields(
                    header_fields_item
                )
            )

        if partial_body_item is not None:
            literal_item = partial_body_item
            literal_content = (
                self._render_partial_body(
                    partial_body_item
                )
            )

        if (
            literal_item is not None
            and literal_content is not None
        ):
            return self._render_literal(
                values=rendered_values,
                content=literal_content,
                item_name=literal_item,
            )

        return IMAPReply(
            f"* {self.sequence_number} FETCH "
            f"({' '.join(rendered_values)})"
        )

    def _render_envelope(
        self,
    ) -> str:
        date = self._envelope_string(
            self._header_value("Date")
        )

        subject = self._envelope_string(
            self._header_value("Subject")
        )

        from_addresses = self._envelope_addresses(
            self._header_values("From")
        )

        sender_values = self._header_values(
            "Sender"
        )

        if sender_values:
            sender_addresses = (
                self._envelope_addresses(
                    sender_values
                )
            )
        else:
            sender_addresses = from_addresses

        reply_to_values = self._header_values(
            "Reply-To"
        )

        if reply_to_values:
            reply_to_addresses = (
                self._envelope_addresses(
                    reply_to_values
                )
            )
        else:
            reply_to_addresses = from_addresses

        to_addresses = self._envelope_addresses(
            self._header_values("To")
        )

        cc_addresses = self._envelope_addresses(
            self._header_values("Cc")
        )

        bcc_addresses = self._envelope_addresses(
            self._header_values("Bcc")
        )

        in_reply_to = self._envelope_string(
            self._header_value("In-Reply-To")
        )

        message_id = self._envelope_string(
            self._header_value("Message-ID")
        )

        return (
            "ENVELOPE "
            "("
            f"{date} "
            f"{subject} "
            f"{from_addresses} "
            f"{sender_addresses} "
            f"{reply_to_addresses} "
            f"{to_addresses} "
            f"{cc_addresses} "
            f"{bcc_addresses} "
            f"{in_reply_to} "
            f"{message_id}"
            ")"
        )   


    def _header_value(
        self,
        name: str,
    ) -> str | None:
        values = self._header_values(
            name
        )

        if not values:
            return None

        return values[0]


    def _header_values(
        self,
        name: str,
    ) -> list[str]:
        for header_name, value in (
            self.entry.message.headers.fields.items()
        ):
            if (
                header_name.casefold()
                != name.casefold()
            ):
                continue

            if isinstance(value, list):
                return [
                    str(item)
                    for item in value
                ]

            return [
                str(value)
            ]

        return []


    @staticmethod
    def _envelope_string(
        value: str | None,
    ) -> str:
        if value is None:
            return "NIL"

        escaped = (
            value
            .replace("\\", "\\\\")
            .replace('"', '\\"')
        )

        return f'"{escaped}"'


    def _envelope_addresses(
        self,
        values: list[str],
    ) -> str:
        if not values:
            return "NIL"

        addresses = getaddresses(
            values
        )

        rendered = []

        for personal_name, address in addresses:
            if "@" in address:
                mailbox, host = address.rsplit(
                    "@",
                    1,
                )
            else:
                mailbox = address
                host = ""

            rendered.append(
                "("
                f"{self._envelope_string(personal_name or None)} "
                "NIL "
                f"{self._envelope_string(mailbox or None)} "
                f"{self._envelope_string(host or None)}"
                ")"
            )

        if not rendered:
            return "NIL"

        return (
            "("
            + " ".join(rendered)
            + ")"
        )

    def _render_partial_body(
        self,
        item: str,
    ) -> bytes:
        if item.startswith(
            "BODY.PEEK[TEXT]<"
        ):
            prefix = "BODY.PEEK[TEXT]<"
            content = self._message_body()

        elif item.startswith(
            "BODY.PEEK[]<"
        ):
            prefix = "BODY.PEEK[]<"
            content = self._message_content()

        elif item.startswith(
            "BODY[TEXT]<"
        ):
            prefix = "BODY[TEXT]<"
            content = self._message_body()

        else:
            prefix = "BODY[]<"
            content = self._message_content()

        partial = item[
            len(prefix):-1
        ]

        try:
            offset_text, count_text = (
                partial.split(
                    ".",
                    1,
                )
            )

            offset = int(offset_text)
            count = int(count_text)

        except ValueError as exc:
            raise IMAPFetchError(
                "Invalid BODY partial"
            ) from exc

        if offset < 0 or count < 0:
            raise IMAPFetchError(
                "Invalid BODY partial"
            )

        return content[
            offset:offset + count
        ]

    def _render_body_header_fields(
        self,
        item: str,
    ) -> bytes:
        exclude = (
            "HEADER.FIELDS.NOT"
            in item
        )

        if item.startswith(
            "BODY.PEEK[HEADER.FIELDS.NOT ("
        ):
            prefix = (
                "BODY.PEEK[HEADER.FIELDS.NOT ("
            )
        elif item.startswith(
            "BODY[HEADER.FIELDS.NOT ("
        ):
            prefix = (
                "BODY[HEADER.FIELDS.NOT ("
            )
        elif item.startswith(
            "BODY.PEEK[HEADER.FIELDS ("
        ):
            prefix = (
                "BODY.PEEK[HEADER.FIELDS ("
            )
        else:
            prefix = (
                "BODY[HEADER.FIELDS ("
            )

        fields_text = item[
            len(prefix):-2
        ]

        requested_fields = {
            field.casefold()
            for field in fields_text.split()
        }

        lines = []

        for name, value in (
            self.entry.message.headers.fields.items()
        ):
            matches = (
                name.casefold()
                in requested_fields
            )

            if exclude:
                if matches:
                    continue
            else:
                if not matches:
                    continue

            if isinstance(value, list):
                for item_value in value:
                    lines.append(
                        f"{name}: {item_value}"
                    )
            else:
                lines.append(
                    f"{name}: {value}"
                )

        return (
            "\r\n".join(lines)
            + "\r\n\r\n"
        ).encode("utf-8")


    def _build_handlers(
        self,
    ) -> dict[str, Callable[[], str | bytes]]:
        return {
            "UID": self._render_uid,
            "FLAGS": self._render_flags,
            "INTERNALDATE": self._render_internaldate,
            "ENVELOPE": self._render_envelope,
            "BODY": self._render_body_structure,
            "RFC822.SIZE": self._render_rfc822_size,
            "RFC822.HEADER": self._render_rfc822_header,
            "RFC822.TEXT": self._render_rfc822_text,
            "RFC822": self._render_rfc822,
            "BODY.PEEK[]": self._render_body_peek,
            "BODY.PEEK[HEADER]": (
                self._render_body_peek_header
            ),
            "BODY.PEEK[TEXT]": (
                self._render_body_peek_text
            ),
            "BODY[HEADER]": self._render_body_header,
            "BODY[TEXT]": self._render_body_text,
            "BODY[]": self._render_body,
        }

    def _render_uid(self) -> str:
        return f"UID {self.entry.uid}"

    def _render_flags(self) -> str:
        return (
            "FLAGS "
            + self.serialize_flags(
                self.entry.flags
            )
        )

    def _render_internaldate(
        self,
    ) -> str:
        value = self.entry.internal_date.strftime(
            "%d-%b-%Y %H:%M:%S %z"
        )

        return f'INTERNALDATE "{value}"'

    def _render_rfc822_size(self) -> str:
        return (
            "RFC822.SIZE "
            f"{len(self._message_content())}"
        )

    def _render_body(self) -> bytes:
        return self._message_content()

    def _message_content(self) -> bytes:
        return (
            MessageSerializer.to_rfc5322(
                self.entry.message
            ).encode("utf-8")
        )

    def _render_body_text(
        self,
    ) -> bytes:
        return self._message_body()

    def _render_body_peek_text(
        self,
    ) -> bytes:
        return self._message_body()

    def _render_literal(
        self,
        values: list[str],
        content: bytes,
        item_name: str,
    ) -> IMAPLiteralResponse:
        prefix_parts = list(values)
        prefix_parts.append(item_name)

        return IMAPLiteralResponse(
            prefix=(
                f"* {self.sequence_number} FETCH "
                f"({' '.join(prefix_parts)}"
            ),
            content=content,
        )

    def _render_body_structure(
        self,
    ) -> str:
        body = self.entry.message.body or ""

        body_bytes = body.encode(
            "utf-8"
        )

        if body:
            line_count = (
                body.count("\n") + 1
            )
        else:
            line_count = 0

        return (
            'BODY ("TEXT" "PLAIN" '
            '("CHARSET" "US-ASCII") '
            'NIL NIL "7BIT" '
            f"{len(body_bytes)} "
            f"{line_count})"
        )

    @staticmethod
    def serialize_flags(
        flags: set[str],
    ) -> str:
        if not flags:
            return "()"

        return (
            "("
            + " ".join(sorted(flags))
            + ")"
        )


    def _render_rfc822(self) -> bytes:
        return self._message_content()


    def _render_rfc822_header(self) -> bytes:
        return self._message_headers()


    def _render_rfc822_text(self) -> bytes:
        return self._message_body()


    def _render_body_peek(self) -> bytes:
        return self._message_content()

    def _render_body_header(
        self,
    ) -> bytes:
        return self._message_headers()

    def _render_body_peek_header(
        self,
    ) -> bytes:
        return self._message_headers()
    

    def _message_headers(self) -> bytes:
        message = self.entry.message

        lines = []

        for name, value in message.headers.fields.items():
            if isinstance(value, list):
                for item in value:
                    lines.append(
                        f"{name}: {item}"
                    )
            else:
                lines.append(
                    f"{name}: {value}"
                )

        return (
            "\r\n".join(lines)
            + "\r\n\r\n"
        ).encode("utf-8")


    def _message_body(self) -> bytes:
        return (
            self.entry.message.body or ""
        ).encode("utf-8")