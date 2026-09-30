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
from garlicsmtp.models import (
    Envelope,
    MailHeaders,
    MailMessage,
)
from garlicsmtp.smtp.mime import MimeAttachment
from garlicsmtp.smtp.mime import (
    MimeAttachment,
    MimeDecoder,
)
from garlicsmtp.storage.store import MessageStore
from garlicsmtp.storage.attachment_store import (
    AttachmentStore,
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


class FakeSentStore:

    def __init__(self):
        self.saved = []

    def save(
        self,
        mailbox,
        message,
    ):
        self.saved.append(
            (
                mailbox,
                message,
            )
        )


def test_mail_composer_saves_accepted_message_as_sent():
    pipeline = FakePipeline()
    sent_store = FakeSentStore()

    composer = MailComposerService(
        pipeline,
        sent_store=sent_store,
    )

    result = composer.send(
        sender="alice@sender.onion",
        recipient="bob@receiver.onion",
        subject="Hello",
        body="Hello from GarlicSMTP",
    )

    assert result is True
    assert len(sent_store.saved) == 1

    mailbox, message = sent_store.saved[0]

    assert mailbox == "alice@sender.onion"
    assert message.envelope.sender == (
        "alice@sender.onion"
    )
    assert message.envelope.recipients == [
        "bob@receiver.onion",
    ]
    assert message.headers.get(
        "Subject"
    ) == "Hello"
    assert message.body == (
        "Hello from GarlicSMTP"
    )


def test_mail_composer_does_not_save_rejected_message_as_sent():
    class RejectingPipeline:

        def execute(
            self,
            context,
        ):
            context.accepted = False
            return context

    sent_store = FakeSentStore()

    composer = MailComposerService(
        RejectingPipeline(),
        sent_store=sent_store,
    )

    result = composer.send(
        sender="alice@sender.onion",
        recipient="bob@receiver.onion",
        subject="Rejected",
        body="This must not be saved",
    )

    assert result is False
    assert sent_store.saved == []


def test_mail_composer_saves_original_message_when_pipeline_replaces_it():
    class TransformingPipeline:

        def execute(
            self,
            context,
        ):
            context.message = MailMessage(
                envelope=Envelope(
                    sender=(
                        context.message
                        .envelope.sender
                    ),
                    recipients=list(
                        context.message
                        .envelope.recipients
                    ),
                ),
                headers=MailHeaders(),
                body="encrypted-payload",
            )

            return context

    sent_store = FakeSentStore()

    composer = MailComposerService(
        TransformingPipeline(),
        sent_store=sent_store,
    )

    result = composer.send(
        sender="alice@sender.onion",
        recipient="bob@receiver.onion",
        subject="Hello",
        body="Hello from GarlicSMTP",
    )

    assert result is True
    assert len(sent_store.saved) == 1

    mailbox, message = sent_store.saved[0]

    assert mailbox == "alice@sender.onion"
    assert message.headers.get(
        "Subject"
    ) == "Hello"
    assert message.body == (
        "Hello from GarlicSMTP"
    )


def test_mail_composer_passes_attachments_to_pipeline():
    pipeline = FakePipeline()

    composer = MailComposerService(
        pipeline,
    )

    attachment = MimeAttachment(
        filename="document.pdf",
        declared_mime="application/pdf",
        content=b"%PDF-1.4\nattachment",
    )

    result = composer.send(
        sender="alice@sender.onion",
        recipient="bob@receiver.onion",
        subject="Attachment",
        body="Hello Bob",
        attachments=[
            attachment,
        ],
    )

    assert result is True
    assert len(pipeline.contexts) == 1
    assert pipeline.contexts[0].attachments == [
        attachment,
    ]


def test_mail_composer_builds_multipart_mixed_for_attachments():
    pipeline = FakePipeline()

    composer = MailComposerService(
        pipeline,
    )

    attachment = MimeAttachment(
        filename="document.pdf",
        declared_mime="application/pdf",
        content=b"%PDF-1.4\nattachment",
    )

    composer.send(
        sender="alice@sender.onion",
        recipient="bob@receiver.onion",
        subject="Attachment",
        body="Hello Bob",
        attachments=[
            attachment,
        ],
    )

    message = pipeline.contexts[0].message

    content_type = message.headers.get(
        "Content-Type"
    )

    assert content_type.startswith(
        "multipart/mixed"
    )

    boundary = (
        content_type
        .split("boundary=", 1)[1]
        .strip()
        .strip('"')
    )

    text, attachments = (
        MimeDecoder.extract_multipart_mixed(
            message.body,
            boundary,
        )
    )

    assert text == "Hello Bob"
    assert attachments == [
        attachment,
    ]


def test_mail_composer_saves_attachment_message_as_plain_sent_message():
    pipeline = FakePipeline()
    sent_store = FakeSentStore()

    composer = MailComposerService(
        pipeline,
        sent_store=sent_store,
    )

    attachment = MimeAttachment(
        filename="document.pdf",
        declared_mime="application/pdf",
        content=b"%PDF-1.4\nattachment",
    )

    result = composer.send(
        sender="alice@sender.onion",
        recipient="bob@receiver.onion",
        subject="Attachment",
        body="Hello Bob",
        attachments=[
            attachment,
        ],
    )

    assert result is True
    assert len(sent_store.saved) == 1

    mailbox, message = sent_store.saved[0]

    assert mailbox == "alice@sender.onion"
    assert message.body == "Hello Bob"
    assert message.headers.get(
        "Content-Type"
    ) is None


def test_mail_composer_stores_sent_attachments(
    tmp_path,
):
    pipeline = FakePipeline()

    attachment_store = AttachmentStore(
        tmp_path / "attachments"
    )

    sent_store = MessageStore(
        attachment_store=attachment_store,
    )

    composer = MailComposerService(
        pipeline,
        sent_store=sent_store,
    )

    attachment = MimeAttachment(
        filename="document.pdf",
        declared_mime="application/pdf",
        content=b"%PDF-1.4\nattachment",
    )

    result = composer.send(
        sender="alice@sender.onion",
        recipient="bob@receiver.onion",
        subject="Attachment",
        body="Hello Bob",
        attachments=[
            attachment,
        ],
    )

    assert result is True

    entries = sent_store.list_entries(
        "alice@sender.onion"
    )

    assert len(entries) == 1

    stored = (
        attachment_store.list_for_message(
            entries[0].id
        )
    )

    assert len(stored) == 1
    assert stored[0].filename == (
        attachment.filename
    )
    assert stored[0].declared_mime == (
        attachment.declared_mime
    )
    assert stored[0].content == (
        attachment.content
    )


def test_mail_composer_rolls_back_sent_when_attachment_save_fails(
    tmp_path,
):
    class FailingAttachmentStore(
        AttachmentStore
    ):

        def __init__(
            self,
            path,
        ):
            super().__init__(path)
            self.save_calls = 0

        def save(
            self,
            **kwargs,
        ):
            self.save_calls += 1

            if self.save_calls == 2:
                raise RuntimeError(
                    "attachment save failed"
                )

            return super().save(
                **kwargs
            )

    attachment_store = FailingAttachmentStore(
        tmp_path / "attachments"
    )

    sent_store = MessageStore(
        attachment_store=attachment_store,
    )

    composer = MailComposerService(
        FakePipeline(),
        sent_store=sent_store,
    )

    attachments = [
        MimeAttachment(
            filename="first.pdf",
            declared_mime="application/pdf",
            content=b"%PDF-1.4\nfirst",
        ),
        MimeAttachment(
            filename="second.pdf",
            declared_mime="application/pdf",
            content=b"%PDF-1.4\nsecond",
        ),
    ]

    with pytest.raises(
        RuntimeError,
        match="attachment save failed",
    ):
        composer.send(
            sender="alice@sender.onion",
            recipient="bob@receiver.onion",
            subject="Attachments",
            body="Hello Bob",
            attachments=attachments,
        )

    assert sent_store.list_entries(
        "alice@sender.onion"
    ) == []

    attachments_path = (
        tmp_path / "attachments"
    )

    assert (
        not attachments_path.exists()
        or not any(
            attachments_path.iterdir()
        )
    )


def test_mail_composer_with_attachment_store_accepts_no_attachments(
    tmp_path,
):
    sent_store = MessageStore(
        attachment_store=AttachmentStore(
            tmp_path / "attachments"
        ),
    )

    composer = MailComposerService(
        FakePipeline(),
        sent_store=sent_store,
    )

    result = composer.send(
        sender="alice@sender.onion",
        recipient="bob@receiver.onion",
        subject="No attachment",
        body="Hello Bob",
    )

    assert result is True

    entries = sent_store.list_entries(
        "alice@sender.onion"
    )

    assert len(entries) == 1