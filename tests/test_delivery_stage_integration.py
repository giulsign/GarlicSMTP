# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.core.pipeline import Pipeline
from garlicsmtp.core.pipeline import PipelineContext
from garlicsmtp.queue.manager import QueueManager
from garlicsmtp.queue.stage import QueueStage
from garlicsmtp.storage.delivery_stage import DeliveryStage
from garlicsmtp.storage.store import MessageStore
from garlicsmtp.storage.entry import VerificationStatus
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
)

from garlicsmtp.security.decryptor import (
    MessageDecryptor,
)
from garlicsmtp.security.encryptor import (
    ENCRYPTION_HEADER,
    MessageEncryptor,
)
from garlicsmtp.security.encryption_key_store import (
    MemoryEncryptionKeyStore,
)


def test_pipeline_delivers_local_message(
    message,
):

    message.envelope.recipients = [
        "bob@test.onion"
    ]

    store = MessageStore()

    queue = QueueManager()

    pipeline = Pipeline()

    pipeline.add(
        DeliveryStage(
            store=store,
            queue_stage=QueueStage(queue),
            local_domains={
                "test.onion",
            },
        )
    )

    pipeline.execute(
        PipelineContext(
            message=message,
        )
    )

    ids = store.list_messages(
        "bob@test.onion"
    )

    assert len(ids) == 1

    assert queue.size() == 0


def test_pipeline_preserves_verified_status_for_local_message(
    message,
):
    message.envelope.recipients = [
        "bob@test.onion"
    ]

    store = MessageStore()
    queue = QueueManager()

    pipeline = Pipeline()
    pipeline.add(
        DeliveryStage(
            store=store,
            queue_stage=QueueStage(queue),
            local_domains={
                "test.onion",
            },
        )
    )

    pipeline.execute(
        PipelineContext(
            message=message,
            verification_status=(
                VerificationStatus.VERIFIED
            ),
        )
    )

    ids = store.list_messages(
        "bob@test.onion"
    )

    assert len(ids) == 1

    entry = store.get_entry(
        "bob@test.onion",
        ids[0],
    )

    assert entry is not None
    assert entry.verification_status == (
        VerificationStatus.VERIFIED
    )

    assert queue.size() == 0


def test_pipeline_encrypts_remote_message_before_queue(
    message,
):
    host = "a" * 56 + ".onion"

    message.envelope.recipients = [
        f"bob@{host}"
    ]

    message.headers.add(
        "Subject",
        "Secret subject",
    )

    message.body = (
        "QUEUE-PLAINTEXT-SENTINEL"
    )

    recipient_private_key = (
        X25519PrivateKey.generate()
    )

    key_store = (
        MemoryEncryptionKeyStore()
    )

    key_store.remember(
        host,
        recipient_private_key
        .public_key()
        .public_bytes_raw(),
    )

    queue = QueueManager()

    stage = DeliveryStage(
        store=MessageStore(),
        queue_stage=QueueStage(queue),
        local_domains={
            "test.onion",
        },
        encryptor=MessageEncryptor(),
        encryption_key_store=key_store,
    )

    stage.process(
        PipelineContext(
            message=message,
        )
    )

    assert queue.size() == 1

    item = queue.dequeue()

    encrypted = item.message

    assert encrypted is not message

    assert (
        encrypted.headers.get(
            ENCRYPTION_HEADER
        )
        is not None
    )

    assert (
        "QUEUE-PLAINTEXT-SENTINEL"
        not in encrypted.body
    )

    assert (
        encrypted.headers.get(
            "Subject"
        )
        is None
    )

    decrypted = MessageDecryptor().decrypt(
        encrypted,
        recipient_private_key,
    )

    assert decrypted.body == (
        "QUEUE-PLAINTEXT-SENTINEL"
    )

    assert decrypted.headers.get(
        "Subject"
    ) == "Secret subject"


def test_pipeline_does_not_queue_remote_plaintext_without_pinned_key(
    message,
):
    host = "b" * 56 + ".onion"

    message.envelope.recipients = [
        f"bob@{host}"
    ]

    message.body = (
        "QUEUE-PLAINTEXT-SENTINEL"
    )

    queue = QueueManager()

    stage = DeliveryStage(
        store=MessageStore(),
        queue_stage=QueueStage(queue),
        local_domains={
            "test.onion",
        },
        encryptor=MessageEncryptor(),
        encryption_key_store=(
            MemoryEncryptionKeyStore()
        ),
    )

    context = stage.process(
        PipelineContext(
            message=message,
        )
    )

    assert queue.size() == 0
    assert context.accepted is False


def test_pipeline_discovers_missing_remote_key_before_queue(
    message,
):
    host = "d" * 56 + ".onion"

    message.envelope.recipients = [
        f"bob@{host}"
    ]

    message.body = (
        "FIRST-CONTACT-PLAINTEXT-SENTINEL"
    )

    recipient_private_key = (
        X25519PrivateKey.generate()
    )

    key_store = MemoryEncryptionKeyStore()

    discovered = []

    def discover_encryption_key(
        hostname,
    ):
        discovered.append(hostname)

        key_store.remember(
            hostname,
            recipient_private_key
            .public_key()
            .public_bytes_raw(),
        )

    queue = QueueManager(
        
    )

    stage = DeliveryStage(
        store=MessageStore(),
        queue_stage=QueueStage(queue),
        local_domains={"local.onion"},
        encryptor=MessageEncryptor(),
        encryption_key_store=key_store,
        discover_encryption_key=(
            discover_encryption_key
        ),
    )

    context = PipelineContext(
        message=message,
    )

    stage.process(context)

    assert discovered == [host]
    assert context.accepted is True
    assert queue.size() == 1

    item = queue.dequeue()

    assert (
        "FIRST-CONTACT-PLAINTEXT-SENTINEL"
        not in item.message.body
    )

    decrypted = MessageDecryptor().decrypt(
        item.message,
        recipient_private_key,
    )

    assert decrypted.body == (
        "FIRST-CONTACT-PLAINTEXT-SENTINEL"
    )