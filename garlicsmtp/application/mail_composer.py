# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from uuid import uuid4

from garlicsmtp.models import (
    Envelope,
    MailHeaders,
    MailMessage,
)
from garlicsmtp.core.pipeline import (
    PipelineContext,
)
from garlicsmtp.smtp.mime import MimeEncoder


class MailComposerService:

    def __init__(
        self,
        pipeline,
        signer=None,
        verifier=None,
        sent_store=None,
    ) -> None:
        self.pipeline = pipeline
        self.signer = signer
        self.verifier = verifier
        self.sent_store = sent_store

    def send(
        self,
        *,
        sender: str,
        recipient: str,
        subject: str,
        body: str,
        attachments=None,
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
                recipients=[recipient],
            ),
            headers=headers,
            body=body,
        )

        sent_headers = MailHeaders()

        for name, value in message.headers.fields.items():
            if isinstance(value, list):
                for item in value:
                    sent_headers.add(
                        name,
                        item,
                    )
            else:
                sent_headers.add(
                    name,
                    value,
                )

        sent_message = MailMessage(
            envelope=Envelope(
                sender=message.envelope.sender,
                recipients=list(
                    message.envelope.recipients
                ),
            ),
            headers=sent_headers,
            body=body,
        )

        if attachments:
            boundary = (
                f"garlicsmtp-{uuid4().hex}"
            )

            message.headers.add(
                "Content-Type",
                (
                    "multipart/mixed; "
                    f'boundary="{boundary}"'
                ),
            )

            message.body = (
                MimeEncoder.encode_multipart_mixed(
                    text=body,  
                    attachments=attachments,
                    boundary=boundary,
                )
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
                message=message,
                attachments=attachments,
            )
        else:
            context = PipelineContext(
                message=message,
                verification_status=(
                    verification_status
                ),
                attachments=attachments,
            )
        #sent_message = message
        context = self.pipeline.execute(
            context
        )

        accepted = bool(
            context.accepted
        )

        if (
            accepted
            and self.sent_store is not None
        ):
            message_id = self.sent_store.save(
                sender,
                sent_message,
            )

            attachment_store = getattr(
                self.sent_store,
                "attachment_store",
                None,
            )

            if attachment_store is not None:
                try:
                    for attachment in (
                            attachments or []
                        ):
                        attachment_store.save(
                            message_id=message_id,
                            filename=attachment.filename,
                            declared_mime=(
                                attachment.declared_mime
                            ),
                            content=attachment.content,
                        )
                except Exception:
                    self.sent_store.delete_entry(
                        sender,
                        message_id,
                    )
                    raise

        return accepted
