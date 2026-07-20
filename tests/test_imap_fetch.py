import pytest

from garlicsmtp.imap import (
    IMAPFetchError,
    IMAPFetchRenderer,
    IMAPLiteralResponse,
    IMAPReply,
)
from garlicsmtp.storage.entry import MessageEntry
from garlicsmtp.storage.serializer import (
    MessageSerializer,
)


def test_imap_fetch_renderer_metadata(
    message,
):
    entry = MessageEntry(
        id="message-id",
        mailbox="bob@test.onion",
        uid=7,
        message=message,
        flags={
            "\\Seen",
        },
    )

    renderer = IMAPFetchRenderer(
        entry=entry,
        sequence_number=2,
    )

    response = renderer.render(
        {
            "UID",
            "FLAGS",
            "RFC822.SIZE",
        }
    )

    assert isinstance(
        response,
        IMAPReply,
    )

    size = len(
        MessageSerializer.to_rfc5322(
            message
        ).encode("utf-8")
    )

    assert response.serialize() == (
        "* 2 FETCH "
        f"(UID 7 FLAGS (\\Seen) "
        f"RFC822.SIZE {size})\r\n"
    )


def test_imap_fetch_renderer_body_literal(
    message,
):
    entry = MessageEntry(
        id="message-id",
        mailbox="bob@test.onion",
        uid=1,
        message=message,
    )

    renderer = IMAPFetchRenderer(
        entry=entry,
        sequence_number=1,
    )

    response = renderer.render(
        {
            "UID",
            "FLAGS",
            "BODY[]",
        }
    )

    assert isinstance(
        response,
        IMAPLiteralResponse,
    )

    assert response.prefix == (
        "* 1 FETCH (UID 1 FLAGS () BODY[]"
    )

    assert response.content == (
        MessageSerializer.to_rfc5322(
            message
        ).encode("utf-8")
    )


def test_imap_fetch_renderer_rejects_unsupported_item(
    message,
):
    entry = MessageEntry(
        id="message-id",
        mailbox="bob@test.onion",
        uid=1,
        message=message,
    )

    renderer = IMAPFetchRenderer(
        entry=entry,
        sequence_number=1,
    )

    with pytest.raises(
        IMAPFetchError,
        match=(
            "Unsupported FETCH item "
            "BODYSTRUCTURE"
        ),
    ):
        renderer.render(
            {
                "BODYSTRUCTURE",
            }
        )


def test_imap_fetch_renderer_uses_stable_item_order(
    message,
):
    entry = MessageEntry(
        id="message-id",
        mailbox="bob@test.onion",
        uid=7,
        message=message,
        flags={
            "\\Seen",
        },
    )

    renderer = IMAPFetchRenderer(
        entry=entry,
        sequence_number=2,
    )

    response = renderer.render(
        {
            "RFC822.SIZE",
            "FLAGS",
            "UID",
        }
    )

    size = len(
        MessageSerializer.to_rfc5322(
            message
        ).encode("utf-8")
    )

    assert response.serialize() == (
        "* 2 FETCH "
        f"(UID 7 FLAGS (\\Seen) "
        f"RFC822.SIZE {size})\r\n"
    )


def test_imap_fetch_renderer_uid_only(
    message,
):
    entry = MessageEntry(
        id="message-id",
        mailbox="bob@test.onion",
        uid=4,
        message=message,
    )

    renderer = IMAPFetchRenderer(
        entry=entry,
        sequence_number=1,
    )

    response = renderer.render(
        {
            "UID",
        }
    )

    assert response.serialize() == (
        "* 1 FETCH (UID 4)\r\n"
    )


def test_imap_fetch_renderer_flags_only(
    message,
):
    entry = MessageEntry(
        id="message-id",
        mailbox="bob@test.onion",
        uid=4,
        message=message,
        flags={
            "\\Flagged",
            "\\Seen",
        },
    )

    renderer = IMAPFetchRenderer(
        entry=entry,
        sequence_number=1,
    )

    response = renderer.render(
        {
            "FLAGS",
        }
    )

    assert response.serialize() == (
        "* 1 FETCH "
        "(FLAGS (\\Flagged \\Seen))\r\n"
    )


def test_imap_fetch_renderer_rfc822_literal(
    message,
):
    message.headers.fields[
        "Subject"
    ] = "RFC822 message"

    message.body = "Full message body"

    entry = MessageEntry(
        id="message-id",
        mailbox="bob@test.onion",
        uid=1,
        message=message,
    )

    renderer = IMAPFetchRenderer(
        entry=entry,
        sequence_number=1,
    )

    response = renderer.render(
        {
            "RFC822",
        }
    )

    assert isinstance(
        response,
        IMAPLiteralResponse,
    )

    assert response.prefix == (
        "* 1 FETCH (RFC822"
    )

    assert response.content == (
        MessageSerializer.to_rfc5322(
            message
        ).encode("utf-8")
    )


def test_imap_fetch_renderer_rfc822_header(
    message,
):
    message.headers.fields[
        "Subject"
    ] = "Header test"

    message.headers.fields[
        "X-Test"
    ] = "value"

    message.body = "Body ignored"

    entry = MessageEntry(
        id="message-id",
        mailbox="bob@test.onion",
        uid=1,
        message=message,
    )

    renderer = IMAPFetchRenderer(
        entry=entry,
        sequence_number=1,
    )

    response = renderer.render(
        {
            "RFC822.HEADER",
        }
    )

    assert isinstance(
        response,
        IMAPLiteralResponse,
    )

    assert response.prefix == (
        "* 1 FETCH (RFC822.HEADER"
    )

    assert response.content == (
        b"Subject: Header test\r\n"
        b"X-Test: value\r\n"
        b"\r\n"
    )


def test_imap_fetch_renderer_rfc822_text(
    message,
):
    message.body = "Only the body"

    entry = MessageEntry(
        id="message-id",
        mailbox="bob@test.onion",
        uid=1,
        message=message,
    )

    renderer = IMAPFetchRenderer(
        entry=entry,
        sequence_number=1,
    )

    response = renderer.render(
        {
            "RFC822.TEXT",
        }
    )

    assert isinstance(
        response,
        IMAPLiteralResponse,
    )

    assert response.prefix == (
        "* 1 FETCH (RFC822.TEXT"
    )

    assert response.content == (
        b"Only the body"
    )


def test_imap_fetch_renderer_body_peek(
    message,
):
    entry = MessageEntry(
        id="message-id",
        mailbox="bob@test.onion",
        uid=1,
        message=message,
    )

    renderer = IMAPFetchRenderer(
        entry=entry,
        sequence_number=1,
    )

    response = renderer.render(
        {
            "BODY.PEEK[]",
        }
    )

    assert isinstance(
        response,
        IMAPLiteralResponse,
    )

    assert response.prefix == (
        "* 1 FETCH (BODY.PEEK[]"
    )

    assert response.content == (
        MessageSerializer.to_rfc5322(
            message
        ).encode("utf-8")
    )


def test_imap_fetch_renderer_combines_uid_and_rfc822(
    message,
):
    entry = MessageEntry(
        id="message-id",
        mailbox="bob@test.onion",
        uid=5,
        message=message,
    )

    renderer = IMAPFetchRenderer(
        entry=entry,
        sequence_number=2,
    )

    response = renderer.render(
        {
            "UID",
            "RFC822",
        }
    )

    assert isinstance(
        response,
        IMAPLiteralResponse,
    )

    assert response.prefix == (
        "* 2 FETCH (UID 5 RFC822"
    )