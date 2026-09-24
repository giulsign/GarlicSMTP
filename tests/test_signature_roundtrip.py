# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import base64
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)

from garlicsmtp.models import (
    Envelope,
    MailHeaders,
    MailMessage,
)
from garlicsmtp.security.signer import (
    MessageSigner,
)
from garlicsmtp.security.verifier import (
    Ed25519MessageVerifier,
)
from garlicsmtp.smtp.engine import (
    SMTPEngine,
)
from garlicsmtp.smtp.session import (
    SMTPSession,
)
from garlicsmtp.smtp.state import (
    SMTPState,
)
from garlicsmtp.storage.entry import (
    VerificationStatus,
)
from garlicsmtp.storage.serializer import (
    MessageSerializer,
)


def test_signed_message_survives_smtp_data_round_trip():
    private_key = Ed25519PrivateKey.generate()

    signer = MessageSigner(
        private_key
    )

    verifier = Ed25519MessageVerifier()

    original = MailMessage(
        envelope=Envelope(
            sender="alice@sender.onion",
            recipients=[
                "bob@receiver.onion",
            ],
        ),
        headers=MailHeaders(
            fields={
                "Subject": "Hello",
            }
        ),
        body="Hello from GarlicSMTP",
    )

    signer.sign(original)

    wire_message = (
        MessageSerializer.to_rfc5322(
            original
        )
    )

    session = SMTPSession(
        client_ip="127.0.0.1"
    )

    session.message.envelope.sender = (
        original.envelope.sender
    )

    session.message.envelope.recipients = list(
        original.envelope.recipients
    )

    session.state = SMTPState.RECEIVE_DATA

    engine = SMTPEngine()

    for line in wire_message.split("\r\n"):
        assert (
            engine.receive_data(
                session,
                line,
            )
            is False
        )

    assert (
        engine.receive_data(
            session,
            ".",
        )
        is True
    )

    assert (
        verifier.verify(
            session.message
        )
        == VerificationStatus.UNKNOWN_KEY
    )


def test_signed_multiline_message_survives_smtp_data_round_trip():
    private_key = Ed25519PrivateKey.generate()

    signer = MessageSigner(
        private_key
    )

    verifier = Ed25519MessageVerifier()

    original = MailMessage(
        envelope=Envelope(
            sender="alice@sender.onion",
            recipients=[
                "bob@receiver.onion",
            ],
        ),
        headers=MailHeaders(
            fields={
                "Subject": "Multiline",
            }
        ),
        body="line one\nline two\nline three",
    )

    signer.sign(original)

    wire_message = (
        MessageSerializer.to_rfc5322(
            original
        )
    )

    session = SMTPSession(
        client_ip="127.0.0.1"
    )

    session.message.envelope.sender = (
        original.envelope.sender
    )

    session.message.envelope.recipients = list(
        original.envelope.recipients
    )

    session.state = SMTPState.RECEIVE_DATA

    engine = SMTPEngine()

    for line in wire_message.split("\r\n"):
        assert (
            engine.receive_data(
                session,
                line,
            )
            is False
        )

    assert (
        engine.receive_data(
            session,
            ".",
        )
        is True
    )

    assert (
        session.message.body
        == original.body
    )

    assert (
        verifier.verify(
            session.message
        )
        == VerificationStatus.UNKNOWN_KEY
    )


def test_signed_message_survives_smtp_dot_stuffing():
    private_key = Ed25519PrivateKey.generate()

    signer = MessageSigner(
        private_key
    )

    verifier = Ed25519MessageVerifier()

    original = MailMessage(
        envelope=Envelope(
            sender="alice@sender.onion",
            recipients=[
                "bob@receiver.onion",
            ],
        ),
        headers=MailHeaders(
            fields={
                "Subject": "Dot stuffing",
            }
        ),
        body=(
            "line one\n"
            ".leading dot\n"
            "..two leading dots\n"
            "line four"
        ),
    )

    signer.sign(original)

    wire_message = (
        MessageSerializer.to_rfc5322(
            original
        )
    )

    session = SMTPSession(
        client_ip="127.0.0.1"
    )

    session.message.envelope.sender = (
        original.envelope.sender
    )

    session.message.envelope.recipients = list(
        original.envelope.recipients
    )

    session.state = SMTPState.RECEIVE_DATA

    engine = SMTPEngine()

    for line in wire_message.split("\r\n"):
        # RFC5321 sender-side dot-stuffing.
        if line.startswith("."):
            line = "." + line

        assert (
            engine.receive_data(
                session,
                line,
            )
            is False
        )

    assert (
        engine.receive_data(
            session,
            ".",
        )
        is True
    )

    assert (
        session.message.body
        == original.body
    )

    assert (
        verifier.verify(
            session.message
        )
        == VerificationStatus.UNKNOWN_KEY
    )


def test_signed_quoted_printable_message_survives_smtp_round_trip():
    private_key = Ed25519PrivateKey.generate()

    signer = MessageSigner(
        private_key
    )

    verifier = Ed25519MessageVerifier()

    original = MailMessage(
        envelope=Envelope(
            sender="alice@sender.onion",
            recipients=[
                "bob@receiver.onion",
            ],
        ),
        headers=MailHeaders(
            fields={
                "Subject": "Quoted printable",
                "Content-Type": "text/plain; charset=utf-8",
                "Content-Transfer-Encoding": "quoted-printable",
            }
        ),
        body="Literal =20 sequence",
    )

    signer.sign(original)

    wire_message = (
        MessageSerializer.to_rfc5322(
            original
        )
    )

    session = SMTPSession(
        client_ip="127.0.0.1"
    )

    session.message.envelope.sender = (
        original.envelope.sender
    )

    session.message.envelope.recipients = list(
        original.envelope.recipients
    )

    session.state = SMTPState.RECEIVE_DATA

    engine = SMTPEngine()

    for line in wire_message.split("\r\n"):
        assert (
            engine.receive_data(
                session,
                line,
            )
            is False
        )

    assert (
        engine.receive_data(
            session,
            ".",
        )
        is True
    )

    assert session.message.body == original.body

    assert (
        verifier.verify(
            session.message
        )
        == VerificationStatus.UNKNOWN_KEY
    )


def test_signed_base64_message_survives_smtp_round_trip():
    private_key = Ed25519PrivateKey.generate()

    signer = MessageSigner(
        private_key
    )

    verifier = Ed25519MessageVerifier()

    original = MailMessage(
        envelope=Envelope(
            sender="alice@sender.onion",
            recipients=[
                "bob@receiver.onion",
            ],
        ),
        headers=MailHeaders(
            fields={
                "Subject": "Base64",
                "Content-Type": "text/plain; charset=utf-8",
                "Content-Transfer-Encoding": "base64",
            }
        ),
        body="Binary-like text: = / + ?",
    )

    signer.sign(original)

    wire_message = (
        MessageSerializer.to_rfc5322(
            original
        )
    )

    expected_wire_body = base64.b64encode(
        original.body.encode("utf-8")
    ).decode("ascii")

    assert expected_wire_body in wire_message
    assert original.body not in wire_message

    session = SMTPSession(
        client_ip="127.0.0.1"
    )

    session.message.envelope.sender = (
        original.envelope.sender
    )

    session.message.envelope.recipients = list(
        original.envelope.recipients
    )

    session.state = SMTPState.RECEIVE_DATA

    engine = SMTPEngine()

    for line in wire_message.split("\r\n"):
        assert (
            engine.receive_data(
                session,
                line,
            )
            is False
        )

    assert (
        engine.receive_data(
            session,
            ".",
        )
        is True
    )

    assert session.message.body == original.body

    assert (
        verifier.verify(
            session.message
        )
        == VerificationStatus.UNKNOWN_KEY
    )


def test_signed_multipart_alternative_survives_smtp_round_trip():
    private_key = Ed25519PrivateKey.generate()

    signer = MessageSigner(
        private_key
    )

    verifier = Ed25519MessageVerifier()

    original = MailMessage(
        envelope=Envelope(
            sender="alice@sender.onion",
            recipients=[
                "bob@receiver.onion",
            ],
        ),
        headers=MailHeaders(
            fields={
                "Subject": "Multipart alternative",
                "Content-Type": (
                    'multipart/alternative; '
                    'boundary="garlic-boundary"'
                ),
            }
        ),
        body="Plain text body",
    )

    signer.sign(original)

    wire_message = (
        MessageSerializer.to_rfc5322(
            original
        )
    )

    assert "--garlic-boundary" in wire_message

    assert (
        "Content-Type: text/plain"
        in wire_message
    )

    assert "--garlic-boundary--" in wire_message

    session = SMTPSession(
        client_ip="127.0.0.1"
    )

    session.message.envelope.sender = (
        original.envelope.sender
    )

    session.message.envelope.recipients = list(
        original.envelope.recipients
    )

    session.state = SMTPState.RECEIVE_DATA

    engine = SMTPEngine()

    for line in wire_message.split("\r\n"):
        assert (
            engine.receive_data(
                session,
                line,
            )
            is False
        )

    assert (
        engine.receive_data(
            session,
            ".",
        )
        is True
    )

    assert session.message.body == original.body

    assert (
        verifier.verify(
            session.message
        )
        == VerificationStatus.UNKNOWN_KEY
    )


def test_signed_message_survives_folded_header_round_trip():
    private_key = Ed25519PrivateKey.generate()

    signer = MessageSigner(
        private_key
    )

    verifier = Ed25519MessageVerifier()

    original = MailMessage(
        envelope=Envelope(
            sender="alice@sender.onion",
            recipients=[
                "bob@receiver.onion",
            ],
        ),
        headers=MailHeaders(
            fields={
                "Subject": "Hello GarlicSMTP world",
            }
        ),
        body="Hello Bob",
    )

    signer.sign(original)

    wire_message = (
        MessageSerializer.to_rfc5322(
            original
        )
    )

    wire_message = wire_message.replace(
        "Subject: Hello GarlicSMTP world",
        "Subject: Hello\r\n GarlicSMTP world",
    )

    session = SMTPSession(
        client_ip="127.0.0.1"
    )

    session.message.envelope.sender = (
        original.envelope.sender
    )

    session.message.envelope.recipients = list(
        original.envelope.recipients
    )

    session.state = SMTPState.RECEIVE_DATA

    engine = SMTPEngine()

    for line in wire_message.split("\r\n"):
        assert (
            engine.receive_data(
                session,
                line,
            )
            is False
        )

    assert (
        engine.receive_data(
            session,
            ".",
        )
        is True
    )

    assert (
        session.message.headers.get("Subject")
        == original.headers.get("Subject")
    )

    assert (
        verifier.verify(
            session.message
        )
        == VerificationStatus.UNKNOWN_KEY
    )