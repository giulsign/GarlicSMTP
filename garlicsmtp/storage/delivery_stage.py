# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.core.pipeline.stage import PipelineStage
from garlicsmtp.queue.stage import QueueStage
from garlicsmtp.storage.store import MessageStore
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PublicKey,
)


class DeliveryStage(PipelineStage):

    def __init__(
        self,
        store: MessageStore,
        queue_stage: QueueStage,
        local_domains: set[str],
        encryptor=None,
        encryption_key_store=None,
        discover_encryption_key=None,
    ):
        self.store = store
        self.queue_stage = queue_stage
        self.local_domains = local_domains
        self.encryptor = encryptor
        self.encryption_key_store = (
            encryption_key_store
        )
        self.discover_encryption_key = (
            discover_encryption_key
        )

    def process(self, context):
        message = context.message

        recipient = message.envelope.recipients[0]

        mailbox, domain = recipient.rsplit(
            "@",
            1,
        )

        if domain in self.local_domains:
            self.store.save_entry(
                recipient,
                message,
                verification_status=(
                    context.verification_status
                ),
            )
            return context

        if (
            self.encryptor is not None
            and self.encryption_key_store
            is not None
        ):
            public_key_bytes = (
                self.encryption_key_store.get(
                    domain
                )
            )

            if (
                public_key_bytes is None
                and self.discover_encryption_key
                is not None
            ):
                self.discover_encryption_key(
                    domain
                )

                public_key_bytes = (
                    self.encryption_key_store.get(
                        domain
                    )
                )

            if public_key_bytes is None:
                context.accepted = False
                context.reject_reason = (
                    "Encryption key unavailable"
                )
                return context

            public_key = (
                X25519PublicKey
                .from_public_bytes(
                    public_key_bytes
                )
            )

            context.message = (
                self.encryptor.encrypt(
                    message,
                    public_key,
                )
            )

        return self.queue_stage.process(
            context
        )