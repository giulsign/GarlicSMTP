# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.application import (
    MessageListViewModel,
)
from garlicsmtp.gui.application import (
    build_view_model,
)


def test_gui_builds_message_list_view_model(
    tmp_path,
    monkeypatch,
):
    view_model = build_view_model()

    assert isinstance(
        view_model.message_list,
        MessageListViewModel,
    )


from types import SimpleNamespace

import garlicsmtp.gui.application as gui_application

from tests.support import (
    make_application_status,
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


class FakeController:

    def __init__(
        self,
        context,
    ):
        self.context = context

    def status(
        self,
    ):
        return make_application_status()


def test_build_view_model_connects_composer_to_application_pipeline(
    monkeypatch,
):
    pipeline = FakePipeline()

    context = SimpleNamespace(
        pipeline=pipeline,
        store=object(),
        signer=None,
    )

    class FakeBuilder:

        def build(
            self,
        ):
            return context

    monkeypatch.setattr(
        gui_application,
        "ApplicationBuilder",
        FakeBuilder,
    )

    monkeypatch.setattr(
        gui_application,
        "ApplicationController",
        FakeController,
    )

    view_model = (
        gui_application.build_view_model()
    )

    assert view_model.compose is not None

    assert (
        view_model.compose
        .composer
        .pipeline
        is pipeline
    )


def test_build_view_model_composer_sends_through_pipeline(
    monkeypatch,
):
    pipeline = FakePipeline()

    context = SimpleNamespace(
        pipeline=pipeline,
        store=object(),
        signer=None,
    )

    class FakeBuilder:

        def build(
            self,
        ):
            return context

    monkeypatch.setattr(
        gui_application,
        "ApplicationBuilder",
        FakeBuilder,
    )

    monkeypatch.setattr(
        gui_application,
        "ApplicationController",
        FakeController,
    )

    view_model = (
        gui_application.build_view_model()
    )

    view_model.compose.sender = (
        "alice@sender.onion"
    )

    view_model.compose.recipient = (
        "bob@receiver.onion"
    )

    view_model.compose.subject = (
        "GUI integration"
    )

    view_model.compose.body = (
        "Hello from GarlicSMTP"
    )

    assert (
        view_model.compose.send()
        is True
    )

    assert len(
        pipeline.contexts
    ) == 1

    message = (
        pipeline.contexts[0]
        .message
    )

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
        == "GUI integration"
    )

    assert (
        message.body
        == "Hello from GarlicSMTP"
    )


def test_build_view_model_connects_composer_to_context_signer(
    monkeypatch,
):
    pipeline = FakePipeline()
    signer = object()
    verifier = object()

    context = SimpleNamespace(
        pipeline=pipeline,
        store=object(),
        signer=signer,
        verifier=verifier,
    )

    class FakeBuilder:

        def build(
            self,
        ):
            return context

    monkeypatch.setattr(
        gui_application,
        "ApplicationBuilder",
        FakeBuilder,
    )

    monkeypatch.setattr(
        gui_application,
        "ApplicationController",
        FakeController,
    )

    view_model = (
        gui_application.build_view_model()
    )

    assert (
        view_model.compose
        .composer
        .signer
        is signer
    )

    assert (
        view_model.compose
        .composer
        .verifier
        is verifier
    )


def test_real_gui_composer_delivers_to_local_mailbox(
    tmp_path,
    monkeypatch,
):
    from garlicsmtp.application import (
        ApplicationBuilder,
    )
    from garlicsmtp.configuration import (
        ApplicationPaths,
        ApplicationSettings,
    )

    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )

    settings = ApplicationSettings()
    settings.tor.enabled = False

    real_builder = ApplicationBuilder(
        paths=paths,
        settings=settings,
    )

    class TestBuilder:

        def build(
            self,
        ):
            return real_builder.build()

    monkeypatch.setattr(
        gui_application,
        "ApplicationBuilder",
        TestBuilder,
    )

    view_model = (
        gui_application.build_view_model()
    )

    context = (
        view_model.controller.context
    )

    try:
        view_model.compose.sender = (
            "alice@test.onion"
        )
        view_model.compose.recipient = (
            "bob@test.onion"
        )
        view_model.compose.subject = (
            "GUI real integration"
        )
        view_model.compose.body = (
            "Delivered through the real pipeline"
        )

        assert (
            view_model.compose.send()
            is True
        )

        entries = context.store.list_entries(
            "bob@test.onion"
        )

        assert len(entries) == 1

        message = entries[0].message

        assert (
            message.envelope.sender
            == "alice@test.onion"
        )

        assert (
            message.envelope.recipients
            == [
                "bob@test.onion",
            ]
        )

        assert (
            message.headers.get(
                "Subject"
            )
            == "GUI real integration"
        )

        assert (
            message.body
            == "Delivered through the real pipeline"
        )
    finally:
        context.queue.backend.close()
        context.store.backend.close()
