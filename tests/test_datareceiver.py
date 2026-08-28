# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.smtp.engine import SMTPEngine
from garlicsmtp.smtp.session import SMTPSession


def test_smtp_engine_receives_text_plain_message():
    engine = SMTPEngine()

    session = SMTPSession("127.0.0.1")

    session.state = session.state.RECEIVE_DATA

    lines = [
        "Subject: Test",
        "Content-Type: text/plain",
        "",
        "Prima riga",
        "Seconda riga",
        ".",
    ]

    for line in lines:
        done = engine.receive_data(
            session,
            line,
        )

        if done:
            break

    assert done is True

    assert session.message.headers.get(
        "Subject"
    ) == "Test"

    assert session.message.headers.get(
        "Content-Type"
    ) == "text/plain"

    assert session.message.body == (
        "Prima riga\n"
        "Seconda riga"
    )


def test_smtp_engine_receives_quoted_printable_text():
    engine = SMTPEngine()

    session = SMTPSession("127.0.0.1")

    session.state = session.state.RECEIVE_DATA

    lines = [
        "Subject: Test",
        "Content-Type: text/plain",
        "Content-Transfer-Encoding: quoted-printable",
        "",
        "Ciao=20Giuliano!",
        ".",
    ]

    for line in lines:
        done = engine.receive_data(
            session,
            line,
        )

        if done:
            break

    assert done is True

    assert session.message.headers.get(
        "Content-Transfer-Encoding"
    ) == "quoted-printable"

    assert session.message.body == (
        "Ciao Giuliano!"
    )


def test_smtp_engine_prefers_plain_text_in_multipart_alternative():
    engine = SMTPEngine()

    session = SMTPSession("127.0.0.1")

    session.state = session.state.RECEIVE_DATA

    lines = [
        "Subject: Multipart Test",
        'Content-Type: multipart/alternative; boundary="abc123"',
        "",
        "--abc123",
        "Content-Type: text/plain; charset=utf-8",
        "",
        "Hello from plain text",
        "--abc123",
        "Content-Type: text/html; charset=utf-8",
        "",
        "<p>Hello from <strong>HTML</strong></p>",
        "--abc123--",
        ".",
    ]

    for line in lines:
        done = engine.receive_data(
            session,
            line,
        )

        if done:
            break

    assert done is True

    assert session.message.headers.get(
        "Content-Type"
    ) == (
        'multipart/alternative; boundary="abc123"'
    )

    assert session.message.body == (
        "Hello from plain text"
    )