import pytest

from garlicsmtp.application.attachment_policy_stage import (
    AttachmentPolicyStage,
)
from garlicsmtp.core.pipeline import (
    PipelineContext,
)
from garlicsmtp.smtp.mime import (
    MimeAttachment,
)


def test_attachment_policy_stage_rejects_invalid_type(
    message,
):
    context = PipelineContext(
        message=message,
        attachments=[
            MimeAttachment(
                filename="document.pdf",
                declared_mime="application/pdf",
                content=b"MZ executable",
            ),
        ],
    )

    stage = AttachmentPolicyStage()

    stage.process(context)

    assert context.accepted is False
    assert context.reject_reason == (
        "Attachment rejected"
    )


def test_attachment_policy_stage_rejects_total_size_over_limit(
    message,
):
    context = PipelineContext(
        message=message,
        attachments=[
            MimeAttachment(
                filename="first.pdf",
                declared_mime="application/pdf",
                content=(
                    b"%PDF-1.4\n"
                    + b"a" * 600_000
                ),
            ),
            MimeAttachment(
                filename="second.pdf",
                declared_mime="application/pdf",
                content=(
                    b"%PDF-1.4\n"
                    + b"b" * 448_576
                ),
            ),
        ],
    )

    stage = AttachmentPolicyStage()

    stage.process(context)

    assert context.accepted is False
    assert context.reject_reason == (
        "Attachment rejected"
    )


def test_attachment_policy_stage_rejects_total_size_over_limit(
    message,
):
    context = PipelineContext(
        message=message,
        attachments=[
            MimeAttachment(
                filename="first.pdf",
                declared_mime="application/pdf",
                content=(
                    b"%PDF-1.4\n"
                    + b"a" * 600_000
                ),
            ),
            MimeAttachment(
                filename="second.pdf",
                declared_mime="application/pdf",
                content=(
                    b"%PDF-1.4\n"
                    + b"b" * 448_576
                ),
            ),
        ],
    )

    stage = AttachmentPolicyStage()

    stage.process(context)

    assert context.accepted is False
    assert context.reject_reason == (
        "Attachment rejected"
    )   


def test_attachment_policy_stage_accepts_valid_attachment(
    message,
):
    attachment = MimeAttachment(
        filename="document.pdf",
        declared_mime="application/pdf",
        content=b"%PDF-1.4\n",
    )

    context = PipelineContext(
        message=message,
        attachments=[
            attachment,
        ],
    )

    stage = AttachmentPolicyStage()

    result = stage.process(context)

    assert result is context
    assert context.accepted is True
    assert context.reject_reason == ""
    assert context.attachments == [
        attachment,
    ]


def test_attachment_policy_stage_accepts_no_attachments(
    message,
):
    context = PipelineContext(
        message=message,
        attachments=None,
    )

    stage = AttachmentPolicyStage()

    result = stage.process(context)

    assert result is context
    assert context.accepted is True
    assert context.reject_reason == ""


def test_attachment_policy_stage_uses_configured_size_limit(
    message,
):
    stage = AttachmentPolicyStage(
        limit_bytes=500_000
    )

    context = PipelineContext(
        message=message,
        attachments=[
            MimeAttachment(
                filename="document.pdf",
                declared_mime="application/pdf",
                content=(
                    b"%PDF-"
                    + b"x" * 599_995
                ),
            ),
        ],
    )

    result = stage.process(context)

    assert result.accepted is False
    assert result.reject_reason == (
        "Attachment rejected"
    )


def test_attachment_policy_stage_rejects_total_size_over_limit(
    message,
):
    context = PipelineContext(
        message=message,
        attachments=[
            MimeAttachment(
                filename="first.pdf",
                declared_mime="application/pdf",
                content=(
                    b"%PDF-1.4\n"
                    + b"a" * 600_000
                ),
            ),
            MimeAttachment(
                filename="second.pdf",
                declared_mime="application/pdf",
                content=(
                    b"%PDF-1.4\n"
                    + b"b" * 448_576
                ),
            ),
        ],
    )

    stage = AttachmentPolicyStage()

    stage.process(context)

    assert context.accepted is False
    assert context.reject_reason == (
        "Attachment rejected"
    )