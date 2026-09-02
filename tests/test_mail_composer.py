# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import pytest

from garlicsmtp.application.mail_composer import (
    MailComposerService,
)
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)

from garlicsmtp.security.signer import (
    MessageSigner,
)
from garlicsmtp.security.signature_header import (
    SIGNATURE_HEADER,
    SignatureHeader,
)
from garlicsmtp.storage.entry import (
    VerificationStatus,
)
from garlicsmtp.security.trust_store import (
    MemoryTrustStore,
)
from garlicsmtp.security.verifier import (
    Ed25519MessageVerifier,
)


class FakePipeline:

    def __init__(self):
        self.contexts = []

    def execute(
        self,
        context,
    ):
        self.contexts.append(
            context
        )

        return context

class FakeSigner:

    def sign(
        self,
        message,
    ):
        message.headers.add(
            "X-Test-Signed",
            "yes",
        )

        return message

class FakeVerifier:

    def __init__(
        self,
        status,
    ):
        self.status = status
        self.messages = []

    def verify(
        self,
        message,
    ):
        self.messages.append(
            message
        )

        return self.status
    
def test_mail_composer_sends_message_through_pipeline():
    pipeline = FakePipeline()

    composer = MailComposerService(
        pipeline
    )

    result = composer.send(
        sender="alice@sender.onion",
        recipient="bob@receiver.onion",
        subject="Hello",
        body="Hello from GarlicSMTP",
    )

    assert result is True

    assert len(
        pipeline.contexts
    ) == 1

    context = pipeline.contexts[0]
    message = context.message

    assert (
        message.envelope.sender
        == "alice@sender.onion"
    )

    assert (
        message.envelope.recipients
        == [
            "bob@receiver.onion",
        ]
    )

    assert (
        message.headers.get(
            "Subject"
        )
        == "Hello"
    )

    assert message.headers.fields == {
        "Subject": "Hello",
    }

    assert (
        message.body
        == "Hello from GarlicSMTP"
    )


def test_mail_composer_rejects_empty_sender():
    composer = MailComposerService(
        FakePipeline()
    )

    with pytest.raises(
        ValueError
    ):
        composer.send(
            sender=" ",
            recipient="bob@receiver.onion",
            subject="Hello",
            body="Test",
        )


def test_mail_composer_rejects_empty_recipient():
    composer = MailComposerService(
        FakePipeline()
    )

    with pytest.raises(
        ValueError
    ):
        composer.send(
            sender="alice@sender.onion",
            recipient=" ",
            subject="Hello",
            body="Test",
        )


def test_mail_composer_does_not_generate_headers_for_empty_subject():
    pipeline = FakePipeline()
    composer = MailComposerService(pipeline)

    composer.send(
        sender="alice@sender.onion",
        recipient="bob@receiver.onion",
        subject="",
        body="Hello",
    )

    message = pipeline.contexts[0].message

    assert message.headers.fields == {}


def test_mail_composer_signs_message_before_pipeline():
    pipeline = FakePipeline()

    composer = MailComposerService(
        pipeline,
        signer=FakeSigner(),
    )

    result = composer.send(
        sender="alice@sender.onion",
        recipient="bob@receiver.onion",
        subject="Hello",
        body="Hello from GarlicSMTP",
    )

    assert result is True

    assert len(
        pipeline.contexts
    ) == 1

    message = pipeline.contexts[0].message

    assert (
        message.headers.get(
            "X-Test-Signed"
        )
        == "yes"
    )


def test_mail_composer_uses_real_message_signer():
    pipeline = FakePipeline()

    signer = MessageSigner(
        Ed25519PrivateKey.generate()
    )

    composer = MailComposerService(
        pipeline,
        signer=signer,
    )

    composer.send(
        sender="alice@sender.onion",
        recipient="bob@receiver.onion",
        subject="Hello",
        body="Hello from GarlicSMTP",
    )

    message = pipeline.contexts[0].message

    value = message.headers.get(
        SIGNATURE_HEADER
    )

    assert value is not None

    header = SignatureHeader.parse(
        value
    )

    assert header.version == 1
    assert header.algorithm == "ed25519"


def test_mail_composer_uses_verifier_status_for_signed_message():
    pipeline = FakePipeline()

    verifier = FakeVerifier(
        VerificationStatus.VERIFIED
    )

    composer = MailComposerService(
        pipeline,
        signer=FakeSigner(),
        verifier=verifier,
    )

    composer.send(
        sender="alice@sender.onion",
        recipient="alice@sender.onion",
        subject="Self delivery",
        body="Hello myself",
    )

    assert len(verifier.messages) == 1

    context = pipeline.contexts[0]

    assert (
        context.verification_status
        == VerificationStatus.VERIFIED
    )


def test_mail_composer_marks_untrusted_local_signature_unknown_key():
    pipeline = FakePipeline()

    private_key = Ed25519PrivateKey.generate()

    signer = MessageSigner(
        private_key
    )

    verifier = Ed25519MessageVerifier(
        trust_store=MemoryTrustStore()
    )

    composer = MailComposerService(
        pipeline,
        signer=signer,
        verifier=verifier,
    )

    composer.send(
        sender="alice@sender.onion",
        recipient="alice@sender.onion",
        subject="Self delivery",
        body="Hello myself",
    )

    context = pipeline.contexts[0]

    assert (
        context.verification_status
        == VerificationStatus.UNKNOWN_KEY
    )


def test_mail_composer_marks_trusted_local_signature_verified():
    pipeline = FakePipeline()

    private_key = Ed25519PrivateKey.generate()

    signer = MessageSigner(
        private_key
    )

    trust_store = MemoryTrustStore()

    public_key = private_key.public_key().public_bytes_raw()

    trust_store.trust(
        "garlicsmtp@sender.onion",
        public_key,
    )

    verifier = Ed25519MessageVerifier(
        trust_store=trust_store
    )

    composer = MailComposerService(
        pipeline,
        signer=signer,
        verifier=verifier,
    )

    composer.send(
        sender="garlicsmtp@sender.onion",
        recipient="garlicsmtp@sender.onion",
        subject="Self delivery",
        body="Hello myself",
    )

    context = pipeline.contexts[0]

    assert (
        context.verification_status
        == VerificationStatus.VERIFIED
    )