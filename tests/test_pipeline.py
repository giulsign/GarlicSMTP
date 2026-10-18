# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import pytest

from garlicsmtp.core.pipeline import Pipeline
from garlicsmtp.core.pipeline import PipelineContext
from garlicsmtp.core.pipeline import LoggerStage

from garlicsmtp.models.envelope import Envelope
from garlicsmtp.models.header import MailHeaders
from garlicsmtp.models import MailMessage


def test_pipeline_logger():

    message = MailMessage(
        envelope=Envelope(
            sender="alice@test.onion",
            recipients=["bob@test.onion"]
        ),
        headers=MailHeaders(),
    )

    pipeline = Pipeline()
    pipeline.add(LoggerStage())

    context = PipelineContext(message)

    pipeline.execute(context)

    assert context.message.envelope.sender == "alice@test.onion"


def test_pipeline_logger_is_privacy_safe(
    capsys,
):
    message = MailMessage(
        envelope=Envelope(
            sender="alice@secret.onion",
            recipients=[
                "bob@private.onion",
            ],
        ),
        headers=MailHeaders(),
        body="very secret body",
    )

    pipeline = Pipeline()
    pipeline.add(
        LoggerStage()
    )

    context = PipelineContext(
        message
    )

    pipeline.execute(
        context
    )

    output = (
        capsys
        .readouterr()
        .out
    )

    assert (
        "PIPELINE message processing started"
        in output
    )

    assert (
        "PIPELINE message accepted"
        in output
    )

    assert output.index(
        "PIPELINE message processing started"
    ) < output.index(
        "PIPELINE message accepted"
    )

    assert (
        "alice@secret.onion"
        not in output
    )

    assert (
        "bob@private.onion"
        not in output
    )

    assert (
        "very secret body"
        not in output
    )


def test_pipeline_context_has_empty_attachments_by_default(
    message,
):
    context = PipelineContext(
        message=message,
    )

    assert context.attachments == []


def test_pipeline_logs_accepted_outcome(message, capsys):
    pipeline = Pipeline()
    context = PipelineContext(message)

    result = pipeline.execute(context)

    output = capsys.readouterr().out

    assert result is context
    assert context.accepted is True
    assert "PIPELINE message accepted" in output


def test_pipeline_logs_rejected_outcome(message, capsys):
    class RejectingStage:
        def process(self, context):
            context.accepted = False
            context.reject_reason = "private rejection detail"

    pipeline = Pipeline()
    pipeline.add(RejectingStage())

    context = PipelineContext(message)

    result = pipeline.execute(context)

    output = capsys.readouterr().out

    assert result is context
    assert context.accepted is False
    assert "PIPELINE message rejected" in output
    assert "private rejection detail" not in output
    assert "PIPELINE message accepted" not in output


def test_pipeline_logs_failure_and_propagates_exception(
    message,
    capsys,
):
    class FailingStage:
        def process(self, context):
            raise RuntimeError("private failure detail")

    pipeline = Pipeline()
    pipeline.add(FailingStage())

    context = PipelineContext(message)

    with pytest.raises(
        RuntimeError,
        match="private failure detail",
    ):
        pipeline.execute(context)

    output = capsys.readouterr().out

    assert "PIPELINE message processing failed" in output
    assert "private failure detail" not in output
    assert "PIPELINE message accepted" not in output