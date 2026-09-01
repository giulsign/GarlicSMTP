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
