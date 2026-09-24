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

        def __init__(
            self,
            *,
            paths,
        ):
            pass

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

        def __init__(
            self,
            *,
            paths,
        ):
            pass

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

        def __init__(
            self,
            *,
            paths,
        ):
            pass

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

        def __init__(
            self,
            *,
            paths,
        ):
            pass

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


def test_run_gui_uses_user_application_paths(
    tmp_path,
    monkeypatch,
):
    from garlicsmtp.configuration import (
        ApplicationPaths,
    )

    expected_paths = ApplicationPaths.for_user(
        home=tmp_path,
    )

    received = {}

    class FakeRoot:

        def __init__(
            self,
        ):
            received["root"] = self
            received["protocol"] = None
            received["mainloop"] = False
            received["destroyed"] = False

        def title(
            self,
            value,
        ):
            received["title"] = value

        def geometry(
            self,
            value,
        ):
            received["geometry"] = value

        def protocol(
            self,
            name,
            callback,
        ):
            received["protocol"] = (
                name,
                callback,
            )

        def mainloop(
            self,
        ):
            received["mainloop"] = True

        def destroy(
            self,
        ):
            received["destroyed"] = True

    class FakeWindow:

        def __init__(
            self,
            master,
            view_model,
        ):
            received["window"] = self
            received["master"] = master
            received["view_model"] = (
                view_model
            )

        def pack(
            self,
            **kwargs,
        ):
            received["pack"] = kwargs

        def close(
            self,
        ):
            received["closed"] = True

    view_model = object()

    def fake_build_view_model(
        *,
        paths=None,
    ):
        received["paths"] = paths
        return view_model

    monkeypatch.setattr(
        gui_application.ApplicationPaths,
        "for_user",
        lambda: expected_paths,
    )

    monkeypatch.setattr(
        gui_application.tk,
        "Tk",
        FakeRoot,
    )

    monkeypatch.setattr(
        gui_application,
        "MainWindow",
        FakeWindow,
    )

    monkeypatch.setattr(
        gui_application,
        "build_view_model",
        fake_build_view_model,
    )

    result = gui_application.run_gui(
        ["garlicsmtp-gui"],
    )

    assert result == 0
    assert received["paths"] == expected_paths
    assert received["master"] is received["root"]
    assert received["view_model"] is view_model

    assert (
        received["title"]
        == "GarlicSMTP Monitor"
    )

    assert received["mainloop"] is True

    assert (
        received["protocol"][0]
        == "WM_DELETE_WINDOW"
    )


def test_run_gui_uses_provided_application_paths(
    tmp_path,
    monkeypatch,
):
    from garlicsmtp.configuration import (
        ApplicationPaths,
    )

    expected_paths = (
        ApplicationPaths.for_development(
            project_root=tmp_path,
            home=tmp_path,
        )
    )

    received = {}

    class FakeRoot:

        def title(
            self,
            value,
        ):
            pass

        def geometry(
            self,
            value,
        ):
            pass

        def protocol(
            self,
            name,
            callback,
        ):
            pass

        def mainloop(
            self,
        ):
            pass

    class FakeWindow:

        def __init__(
            self,
            master,
            view_model,
        ):
            pass

        def pack(
            self,
            **kwargs,
        ):
            pass

        def close(
            self,
        ):
            pass

    def fake_build_view_model(
        *,
        paths=None,
    ):
        received["paths"] = paths
        return object()

    monkeypatch.setattr(
        gui_application.tk,
        "Tk",
        FakeRoot,
    )

    monkeypatch.setattr(
        gui_application,
        "MainWindow",
        FakeWindow,
    )

    monkeypatch.setattr(
        gui_application,
        "build_view_model",
        fake_build_view_model,
    )

    result = gui_application.run_gui(
        ["garlicsmtp-gui"],
        paths=expected_paths,
    )

    assert result == 0
    assert received["paths"] == expected_paths


def test_build_view_model_uses_provided_application_paths(
    tmp_path,
    monkeypatch,
):
    from garlicsmtp.configuration import (
        ApplicationPaths,
    )

    expected_paths = (
        ApplicationPaths.for_development(
            project_root=tmp_path,
            home=tmp_path,
        )
    )

    context = SimpleNamespace(
        pipeline=FakePipeline(),
        store=object(),
        signer=None,
    )

    received = {}

    class FakeBuilder:

        def __init__(
            self,
            *,
            paths,
        ):
            received["paths"] = paths

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

    gui_application.build_view_model(
        paths=expected_paths,
    )

    assert received["paths"] == expected_paths


def test_run_gui_closes_window_before_destroying_root(
    monkeypatch,
):
    events = []
    received = {}

    class FakeRoot:

        def title(
            self,
            value,
        ):
            pass

        def geometry(
            self,
            value,
        ):
            pass

        def protocol(
            self,
            name,
            callback,
        ):
            received["close_callback"] = callback

        def mainloop(
            self,
        ):
            received["close_callback"]()

        def destroy(
            self,
        ):
            events.append("destroy")

    class FakeWindow:

        def __init__(
            self,
            master,
            view_model,
        ):
            pass

        def pack(
            self,
            **kwargs,
        ):
            pass

        def close(
            self,
        ):
            events.append("close")

    monkeypatch.setattr(
        gui_application.tk,
        "Tk",
        FakeRoot,
    )

    monkeypatch.setattr(
        gui_application,
        "MainWindow",
        FakeWindow,
    )

    monkeypatch.setattr(
        gui_application,
        "build_view_model",
        lambda **kwargs: object(),
    )

    result = gui_application.run_gui(
        ["garlicsmtp-gui"],
        paths=object(),
    )

    assert result == 0

    assert events == [
        "close",
        "destroy",
    ]


def test_gui_package_exports_tk_main_window():
    import garlicsmtp.gui as gui

    from garlicsmtp.gui.tk_main_window import (
        MainWindow as TkMainWindow,
    )

    assert gui.MainWindow is TkMainWindow