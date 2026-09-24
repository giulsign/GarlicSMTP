# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.application.compose_view_model import (
    ComposeViewModel,
)


class FakeComposer:

    def __init__(self):
        self.calls = []

    def send(
        self,
        *,
        sender,
        recipient,
        subject,
        body,
    ):
        self.calls.append(
            {
                "sender": sender,
                "recipient": recipient,
                "subject": subject,
                "body": body,
            }
        )

        return True


def test_compose_view_model_sends_message():
    composer = FakeComposer()

    view_model = ComposeViewModel(
        composer
    )

    view_model.sender = (
        "alice@sender.onion"
    )

    view_model.recipient = (
        "bob@receiver.onion"
    )

    view_model.subject = "Hello"

    view_model.body = (
        "Hello from GarlicSMTP"
    )

    result = view_model.send()

    assert result is True

    assert composer.calls == [
        {
            "sender": (
                "alice@sender.onion"
            ),
            "recipient": (
                "bob@receiver.onion"
            ),
            "subject": "Hello",
            "body": (
                "Hello from GarlicSMTP"
            ),
        }
    ]


def test_compose_view_model_clears_after_successful_send():
    composer = FakeComposer()

    view_model = ComposeViewModel(
        composer
    )

    view_model.sender = (
        "alice@sender.onion"
    )
    view_model.recipient = (
        "bob@receiver.onion"
    )
    view_model.subject = "Hello"
    view_model.body = "Body"

    assert view_model.send() is True

    assert view_model.sender == ""
    assert view_model.recipient == ""
    assert view_model.subject == ""
    assert view_model.body == ""


def test_compose_view_model_sets_default_sender():
    composer = FakeComposer()

    view_model = ComposeViewModel(
        composer
    )

    hostname = (
        ("a" * 56)
        + ".onion"
    )

    view_model.set_default_sender(
        hostname
    )

    assert view_model.sender == (
        "garlicsmtp@"
        + hostname
    )


def test_compose_view_model_does_not_replace_existing_sender():
    composer = FakeComposer()

    view_model = ComposeViewModel(
        composer
    )

    view_model.sender = (
        "alice@example.onion"
    )

    view_model.set_default_sender(
        ("a" * 56)
        + ".onion"
    )

    assert view_model.sender == (
        "alice@example.onion"
    )