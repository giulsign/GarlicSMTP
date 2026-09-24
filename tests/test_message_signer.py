# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import base64
import pytest
from cryptography.exceptions import (
    InvalidSignature,
)
from garlicsmtp.security.signature_header import (
    SignatureHeader,
)
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)

from garlicsmtp.models import (
    Envelope,
    MailHeaders,
    MailMessage,
)
from garlicsmtp.security.signature_header import (
    SIGNATURE_HEADER,
)
from garlicsmtp.security.signer import MessageSigner
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PublicKey,
)
from garlicsmtp.security.canonicalizer import (
    MessageCanonicalizer,
)


def test_message_signer_adds_signature_header():
    private_key = Ed25519PrivateKey.generate()

    signer = MessageSigner(
        private_key
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

    result = signer.sign(message)

    assert result is message

    value = message.headers.get(
        SIGNATURE_HEADER
    )

    assert value is not None



def test_message_signer_writes_valid_ed25519_material():
    private_key = Ed25519PrivateKey.generate()

    signer = MessageSigner(
        private_key
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

    signer.sign(message)

    header = SignatureHeader.parse(
        message.headers.get(
            SIGNATURE_HEADER
        )
    )

    public_key = base64.b64decode(
        header.public_key,
        validate=True,
    )

    signature = base64.b64decode(
        header.signature,
        validate=True,
    )

    assert header.version == 1
    assert header.algorithm == "ed25519"
    assert len(public_key) == 32
    assert len(signature) == 64


def test_message_signer_signature_verifies():
    private_key = Ed25519PrivateKey.generate()

    signer = MessageSigner(
        private_key
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

    signer.sign(message)

    header = SignatureHeader.parse(
        message.headers.get(
            SIGNATURE_HEADER
        )
    )

    public_key_bytes = base64.b64decode(
        header.public_key,
        validate=True,
    )

    signature = base64.b64decode(
        header.signature,
        validate=True,
    )

    public_key = Ed25519PublicKey.from_public_bytes(
        public_key_bytes
    )

    canonical = MessageCanonicalizer.canonicalize(
        message
    )

    public_key.verify(
        signature,
        canonical,
    )


def test_message_signer_detects_modified_body():
    private_key = Ed25519PrivateKey.generate()

    signer = MessageSigner(
        private_key
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

    signer.sign(message)

    header = SignatureHeader.parse(
        message.headers.get(
            SIGNATURE_HEADER
        )
    )

    public_key = (
        Ed25519PublicKey.from_public_bytes(
            base64.b64decode(
                header.public_key,
                validate=True,
            )
        )
    )

    signature = base64.b64decode(
        header.signature,
        validate=True,
    )

    # Tampering after signing.
    message.body = "Modified by Mallory"

    canonical = (
        MessageCanonicalizer.canonicalize(
            message
        )
    )

    with pytest.raises(
        InvalidSignature
    ):
        public_key.verify(
            signature,
            canonical,
        )