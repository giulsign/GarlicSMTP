# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import base64
import pytest

from garlicsmtp.security.verifier import (
    MessageVerifier,
)
from garlicsmtp.models import (
    Envelope,
    MailHeaders,
    MailMessage,
)
from garlicsmtp.storage.entry import (
    VerificationStatus,
)
from garlicsmtp.security.verifier import (
    Ed25519MessageVerifier,
)
from garlicsmtp.security.signature_header import (
    SIGNATURE_HEADER,
)
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)

from garlicsmtp.security.signature_header import (
    SignatureHeader,
)
from garlicsmtp.security.signer import (
    MessageSigner,
)
from garlicsmtp.security.trust_store import (
    MemoryTrustStore,
)

def test_message_verifier_is_abstract():
    with pytest.raises(TypeError):
        MessageVerifier()




def test_message_verifier_returns_unsigned_without_signature():
    verifier = Ed25519MessageVerifier()

    message = MailMessage(
        envelope=Envelope(
            sender="alice@test.onion",
            recipients=[
                "bob@test.onion",
            ],
        ),
        headers=MailHeaders(
            fields={
                "Subject": "Hello",
            }
        ),
        body="Hello Bob",
    )

    assert (
        verifier.verify(message)
        == VerificationStatus.UNSIGNED
    )


def test_message_verifier_returns_invalid_for_malformed_header():
    verifier = Ed25519MessageVerifier()

    message = MailMessage(
        envelope=Envelope(
            sender="alice@test.onion",
            recipients=[
                "bob@test.onion",
            ],
        ),
        headers=MailHeaders(
            fields={
                "Subject": "Hello",
                SIGNATURE_HEADER: (
                    "this is not a valid signature"
                ),
            }
        ),
        body="Hello Bob",
    )

    assert (
        verifier.verify(message)
        == VerificationStatus.INVALID
    )


def test_message_verifier_returns_invalid_for_invalid_base64():
    verifier = Ed25519MessageVerifier()

    message = MailMessage(
        envelope=Envelope(
            sender="alice@test.onion",
            recipients=[
                "bob@test.onion",
            ],
        ),
        headers=MailHeaders(
            fields={
                "Subject": "Hello",
                SIGNATURE_HEADER: (
                    "v=1; "
                    "alg=ed25519; "
                    "key=!!!not-base64!!!; "
                    "sig=!!!not-base64!!!"
                ),
            }
        ),
        body="Hello Bob",
    )

    assert (
        verifier.verify(message)
        == VerificationStatus.INVALID
    )



def test_message_verifier_returns_invalid_for_wrong_key_or_signature_length():
    verifier = Ed25519MessageVerifier()

    message = MailMessage(
        envelope=Envelope(
            sender="alice@test.onion",
            recipients=[
                "bob@test.onion",
            ],
        ),
        headers=MailHeaders(
            fields={
                "Subject": "Hello",
                SIGNATURE_HEADER: (
                    "v=1; "
                    "alg=ed25519; "
                    "key=YWJj; "
                    "sig=ZGVm"
                ),
            }
        ),
        body="Hello Bob",
    )

    assert (
        verifier.verify(message)
        == VerificationStatus.INVALID
    )



def test_message_verifier_returns_invalid_for_bad_signature():
    private_key = Ed25519PrivateKey.generate()

    public_key = private_key.public_key().public_bytes_raw()

    bad_signature = b"\x00" * 64

    signature_header = SignatureHeader(
        version=1,
        algorithm="ed25519",
        public_key=base64.b64encode(
            public_key
        ).decode("ascii"),
        signature=base64.b64encode(
            bad_signature
        ).decode("ascii"),
    )

    message = MailMessage(
        envelope=Envelope(
            sender="alice@test.onion",
            recipients=[
                "bob@test.onion",
            ],
        ),
        headers=MailHeaders(
            fields={
                "Subject": "Hello",
                SIGNATURE_HEADER: (
                    signature_header.serialize()
                ),
            }
        ),
        body="Hello Bob",
    )

    assert (
        Ed25519MessageVerifier().verify(
            message
        )
        == VerificationStatus.INVALID
    )



def test_message_verifier_returns_unknown_key_for_valid_signature():
    private_key = Ed25519PrivateKey.generate()

    message = MailMessage(
        envelope=Envelope(
            sender="alice@test.onion",
            recipients=[
                "bob@test.onion",
            ],
        ),
        headers=MailHeaders(
            fields={
                "Subject": "Hello",
            }
        ),
        body="Hello Bob",
    )

    MessageSigner(
        private_key
    ).sign(message)

    assert (
        Ed25519MessageVerifier().verify(
            message
        )
        == VerificationStatus.UNKNOWN_KEY
    )


def test_message_verifier_returns_verified_for_trusted_sender_key():
    private_key = Ed25519PrivateKey.generate()

    message = MailMessage(
        envelope=Envelope(
            sender="alice@test.onion",
            recipients=[
                "bob@test.onion",
            ],
        ),
        headers=MailHeaders(
            fields={
                "Subject": "Hello",
            }
        ),
        body="Hello Bob",
    )

    MessageSigner(
        private_key
    ).sign(message)

    public_key = (
        private_key
        .public_key()
        .public_bytes_raw()
    )

    trust_store = MemoryTrustStore()

    trust_store.trust(
        "alice@test.onion",
        public_key,
    )

    verifier = Ed25519MessageVerifier(
        trust_store=trust_store
    )

    assert (
        verifier.verify(message)
        == VerificationStatus.VERIFIED
    )


def test_message_verifier_returns_unknown_key_for_changed_sender_key():
    trusted_private_key = Ed25519PrivateKey.generate()
    different_private_key = Ed25519PrivateKey.generate()

    trust_store = MemoryTrustStore()

    trust_store.trust(
        "alice@test.onion",
        trusted_private_key
        .public_key()
        .public_bytes_raw(),
    )

    message = MailMessage(
        envelope=Envelope(
            sender="alice@test.onion",
            recipients=[
                "bob@test.onion",
            ],
        ),
        headers=MailHeaders(
            fields={
                "Subject": "Hello",
            }
        ),
        body="Hello Bob",
    )

    MessageSigner(
        different_private_key
    ).sign(message)

    verifier = Ed25519MessageVerifier(
        trust_store=trust_store
    )

    assert (
        verifier.verify(message)
        == VerificationStatus.UNKNOWN_KEY
    )


def test_verifier_accepts_signature_header_case_insensitively():
    private_key = Ed25519PrivateKey.generate()

    signer = MessageSigner(
        private_key
    )

    message = MailMessage(
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
        body="Hello",
    )

    signer.sign(message)

    signature = message.headers.fields.pop(
        "X-GarlicSMTP-Signature"
    )

    message.headers.fields[
        "x-garlicsmtp-signature"
    ] = signature

    verifier = Ed25519MessageVerifier()

    assert (
        verifier.verify(message)
        == VerificationStatus.UNKNOWN_KEY
    )