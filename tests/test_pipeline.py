# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

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
        "PIPELINE message accepted"
        in output
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

