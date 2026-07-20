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


class IMAPFetchError(ValueError):
    pass


@dataclass(slots=True)
class IMAPFetchRenderer:

    entry: MessageEntry
    sequence_number: int
    mark_seen: bool = False

    SEEN_ITEMS = {
        "BODY[]",
        "RFC822",
        "RFC822.TEXT",
    }

    ITEM_ORDER = (
        "UID",
        "FLAGS",
        "RFC822.SIZE",
        "RFC822.HEADER",
        "RFC822.TEXT",
        "RFC822",
        "BODY.PEEK[]",
        "BODY[]",
    )

    def render(
        self,
        requested_items: set[str],
    ) -> IMAPResponse:
        handlers = self._build_handlers()

        unsupported = (
            requested_items
            - handlers.keys()
        )

        if unsupported:
            item = sorted(unsupported)[0]

            raise IMAPFetchError(
                f"Unsupported FETCH item {item}"
            )

        self.mark_seen = bool(requested_items & self.SEEN_ITEMS)

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

    def _build_handlers(
        self,
    ) -> dict[str, Callable[[], str | bytes]]:
        return {
            "UID": self._render_uid,
            "FLAGS": self._render_flags,
            "RFC822.SIZE": self._render_rfc822_size,
            "RFC822.HEADER": self._render_rfc822_header,
            "RFC822.TEXT": self._render_rfc822_text,
            "RFC822": self._render_rfc822,
            "BODY.PEEK[]": self._render_body_peek,
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