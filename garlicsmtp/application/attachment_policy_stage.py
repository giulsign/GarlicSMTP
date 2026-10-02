# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.application.attachment_policy import (
    AttachmentTypeRejected,
    validate_attachment_type,
)
from garlicsmtp.core.pipeline.stage import (
    PipelineStage,
)
from garlicsmtp.application.attachment_limit import (
    ATTACHMENT_LIMIT_BYTES,
    AttachmentLimitExceeded,
    validate_attachment_sizes,
)


class AttachmentPolicyStage(
    PipelineStage
):

    def __init__(
        self,
        *,
        limit_bytes=ATTACHMENT_LIMIT_BYTES,
    ):
        self.limit_bytes = limit_bytes


    def process(
        self,
        context,
    ):
        attachments = (
            context.attachments or []
        )

        try:
            validate_attachment_sizes(
                [
                    len(attachment.content)
                    for attachment
                    in attachments
                ],
                limit_bytes=self.limit_bytes,
            )

            for attachment in attachments:
                validate_attachment_type(
                    filename=attachment.filename,
                    declared_mime=(
                        attachment.declared_mime
                    ),
                    content=attachment.content,
                )

        except (
            AttachmentLimitExceeded,
            AttachmentTypeRejected,
        ):
            context.accepted = False
            context.reject_reason = (
                "Attachment rejected"
            )

        return context
