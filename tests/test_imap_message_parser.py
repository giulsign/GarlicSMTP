import pytest

from garlicsmtp.imap.message_parser import (
    IMAPMessageParseError,
    IMAPMessageParser,
)


def test_imap_message_parser_parses_message():
    message = IMAPMessageParser.parse(
        (
            b"From: Alice <alice@test.onion>\r\n"
            b"To: Bob <bob@test.onion>\r\n"
            b"Subject: APPEND test\r\n"
            b"\r\n"
            b"Stored through IMAP."
        )
    )

    assert message.envelope.sender == (
        "alice@test.onion"
    )

    assert message.envelope.recipients == [
        "bob@test.onion",
    ]

    assert message.body == (
        "Stored through IMAP."
    )


def test_imap_message_parser_parses_multiple_recipients():
    message = IMAPMessageParser.parse(
        (
            b"From: alice@test.onion\r\n"
            b"To: bob@test.onion, "
            b"carol@test.onion\r\n"
            b"Cc: dave@test.onion\r\n"
            b"\r\n"
            b"Message body"
        )
    )

    assert message.envelope.recipients == [
        "bob@test.onion",
        "carol@test.onion",
        "dave@test.onion",
    ]


def test_imap_message_parser_allows_missing_envelope_headers():
    message = IMAPMessageParser.parse(
        (
            b"Subject: Draft message\r\n"
            b"\r\n"
            b"Draft body"
        )
    )

    assert message.envelope.sender == ""
    assert message.envelope.recipients == []
    assert message.body == "Draft body"


def test_imap_message_parser_parses_multipart_plain_body():
    message = IMAPMessageParser.parse(
        (
            b"From: alice@test.onion\r\n"
            b"To: bob@test.onion\r\n"
            b"Content-Type: multipart/alternative; "
            b'boundary="test-boundary"\r\n'
            b"\r\n"
            b"--test-boundary\r\n"
            b"Content-Type: text/plain; charset=utf-8\r\n"
            b"\r\n"
            b"Plain body\r\n"
            b"--test-boundary\r\n"
            b"Content-Type: text/html; charset=utf-8\r\n"
            b"\r\n"
            b"<p>HTML body</p>\r\n"
            b"--test-boundary--\r\n"
        )
    )

    assert message.body.strip() == (
        "Plain body"
    )


def test_imap_message_parser_rejects_empty_literal():
    with pytest.raises(
        IMAPMessageParseError,
        match="APPEND literal is empty",
    ):
        IMAPMessageParser.parse(
            b""
        )