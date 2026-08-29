# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import pytest

from garlicsmtp.application.mail_composer import (
    MailComposerService,
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