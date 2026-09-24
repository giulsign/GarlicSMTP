# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.models import (
    Envelope,
    MailHeaders,
    MailMessage,
)
from garlicsmtp.core.pipeline import (
    PipelineContext,
)


class MailComposerService:

    def __init__(
        self,
        pipeline,
        signer=None,
        verifier=None,
    ) -> None:
        self.pipeline = pipeline
        self.signer = signer
        self.verifier = verifier

    def send(
        self,
        *,
        sender: str,
        recipient: str,
        subject: str,
        body: str,
    ) -> bool:
        sender = sender.strip()
        recipient = recipient.strip()

        if not sender:
            raise ValueError(
                "sender cannot be empty"
            )

        if not recipient:
            raise ValueError(
                "recipient cannot be empty"
            )

        headers = MailHeaders()

        if subject:
            headers.add(
                "Subject",
                subject,
            )

        message = MailMessage(
            envelope=Envelope(
                sender=sender,
                recipients=[
                    recipient,
                ],
            ),
            headers=headers,
            body=body,
        )

        verification_status = None

        if self.signer is not None:
            message = self.signer.sign(
                message
            )

            if self.verifier is not None:
                verification_status = (
                    self.verifier.verify(
                        message
                    )
                )

        if verification_status is None:
            context = PipelineContext(
                message=message
            )
        else:
            context = PipelineContext(
                message=message,
                verification_status=(
                    verification_status
                ),
            )

        context = self.pipeline.execute(
            context
        )

        return bool(
            context.accepted
        )
