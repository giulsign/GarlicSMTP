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
from garlicsmtp.configuration import (
    ApplicationPaths,
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


def test_gui_builds_received_and_sent_message_view_models():
    view_model = build_view_model()

    context = (
        view_model.controller.context
    )

    assert isinstance(
        view_model.received_message_list,
        MessageListViewModel,
    )
    assert isinstance(
        view_model.sent_message_list,
        MessageListViewModel,
    )

    assert (
        view_model.received_message_list
        is not view_model.sent_message_list
    )

    assert (
        view_model.received_message_preview
        is not view_model.sent_message_preview
    )

    assert (
        view_model.received_message_list
        .explorer.store
        is context.store
    )
    assert (
        view_model.received_message_preview
        .explorer.store
        is context.store
    )
    assert (
        view_model.sent_message_list
        .explorer.store
        is not context.store
    )
    assert (
        view_model.sent_message_preview
        .explorer.store
        is not context.store
    )
    assert (
        view_model.sent_message_list
        .explorer.store
        is view_model.sent_message_preview
        .explorer.store
    )

    assert (
        view_model.message_list
        is view_model.received_message_list
    )
    assert (
        view_model.message_preview
        is view_model.received_message_preview
    )


def test_real_gui_self_send_separates_received_and_sent_mail(
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
            "alice@test.onion"
        )
        view_model.compose.subject = (
            "Self test"
        )
        view_model.compose.body = (
            "Self delivery"
        )

        assert (
            view_model.compose.send()
            is True
        )

        received_store = (
            view_model.received_message_list
            .explorer.store
        )
        sent_store = (
            view_model.sent_message_list
            .explorer.store
        )

        received_entries = (
            received_store.list_entries(
                "alice@test.onion"
            )
        )
        sent_entries = (
            sent_store.list_entries(
                "alice@test.onion"
            )
        )

        assert received_store is context.store
        assert sent_store is not context.store

        assert (
            sent_store.attachment_store
            is not None
        )

        assert len(received_entries) == 1
        assert len(sent_entries) == 1

        assert (
            received_entries[0].message.body
            == "Self delivery"
        )
        assert (
            sent_entries[0].message.body
            == "Self delivery"
        )
    finally:
        context.queue.backend.close()
        context.store.backend.close()


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
    tmp_path,
    monkeypatch,
):
    pipeline = FakePipeline()

    context = SimpleNamespace(
        pipeline=pipeline,
        store=object(),
        signer=None,
        paths=ApplicationPaths(
            root_dir=tmp_path / "garlicsmtp",
        ),
    )

    context.paths.data_dir.mkdir(
        parents=True,
        exist_ok=True,
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
    tmp_path,
):

    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )
    pipeline = FakePipeline()

    context = SimpleNamespace(
        pipeline=pipeline,
        store=object(),
        signer=None,
        paths=paths,
    )

    context.paths.data_dir.mkdir(
        parents=True,
        exist_ok=True,
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
    tmp_path,
):

    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )
    pipeline = FakePipeline()
    signer = object()
    verifier = object()

    context = SimpleNamespace(
        pipeline=pipeline,
        store=object(),
        signer=signer,
        verifier=verifier,
        paths=paths,
    )

    context.paths.data_dir.mkdir(
        parents=True,
        exist_ok=True,
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


def test_real_gui_composer_separates_received_and_sent_mail(
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
            "Sent and received"
        )
        view_model.compose.body = (
            "GarlicSMTP dual mailbox test"
        )

        assert (
            view_model.compose.send()
            is True
        )

        received_store = (
            view_model.received_message_list
            .explorer.store
        )
        sent_store = (
            view_model.sent_message_list
            .explorer.store
        )

        assert received_store is context.store
        assert sent_store is not context.store

        received_entries = (
            received_store.list_entries(
                "bob@test.onion"
            )
        )
        sent_entries = (
            sent_store.list_entries(
                "alice@test.onion"
            )
        )

        assert (
            context.store.list_entries(
                "alice@test.onion"
            )
            == []
        )

        assert len(received_entries) == 1
        assert len(sent_entries) == 1

        received_message = (
            received_entries[0].message
        )
        sent_message = (
            sent_entries[0].message
        )

        assert (
            received_message.envelope.sender
            == "alice@test.onion"
        )
        assert (
            sent_message.envelope.sender
            == "alice@test.onion"
        )

        assert (
            received_message.envelope.recipients
            == ["bob@test.onion"]
        )
        assert (
            sent_message.envelope.recipients
            == ["bob@test.onion"]
        )

        assert (
            received_message.headers.get(
                "Subject"
            )
            == "Sent and received"
        )
        assert (
            sent_message.headers.get(
                "Subject"
            )
            == "Sent and received"
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
            *,
            folder_opener,
        ):
            received["window"] = self
            received["master"] = master
            received["view_model"] = (
                view_model
            )
            received["folder_opener"] = folder_opener

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

    assert received["folder_opener"] is not None

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
            *,
            folder_opener,
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
        paths=expected_paths,
    )

    context.paths.data_dir.mkdir(
        parents=True,
        exist_ok=True,
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
            *,
            folder_opener,
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


def test_real_gui_sent_mail_persists_across_rebuild(
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

    class TestBuilder:

        def __init__(
            self,
            *,
            paths,
        ):
            self.builder = ApplicationBuilder(
                paths=paths,
                settings=settings,
            )

        def build(
            self,
        ):
            return self.builder.build()

    monkeypatch.setattr(
        gui_application,
        "ApplicationBuilder",
        TestBuilder,
    )

    first_view_model = (
        gui_application.build_view_model(
            paths=paths,
        )
    )

    first_context = (
        first_view_model.controller.context
    )

    try:
        first_view_model.compose.sender = (
            "alice@test.onion"
        )
        first_view_model.compose.recipient = (
            "bob@test.onion"
        )
        first_view_model.compose.subject = (
            "Persistent sent"
        )
        first_view_model.compose.body = (
            "This sent message must survive rebuild"
        )

        assert (
            first_view_model.compose.send()
            is True
        )

        first_sent_store = (
            first_view_model.sent_message_list
            .explorer.store
        )

        assert len(
            first_sent_store.list_entries(
                "alice@test.onion"
            )
        ) == 1

    finally:
        first_context.queue.backend.close()
        first_context.store.backend.close()
        first_sent_store.backend.close()

    second_view_model = (
        gui_application.build_view_model(
            paths=paths,
        )
    )

    second_context = (
        second_view_model.controller.context
    )

    try:
        second_sent_store = (
            second_view_model.sent_message_list
            .explorer.store
        )

        sent_entries = (
            second_sent_store.list_entries(
                "alice@test.onion"
            )
        )

        assert len(sent_entries) == 1

        assert (
            sent_entries[0].message.body
            == "This sent message must survive rebuild"
        )

    finally:
        second_context.queue.backend.close()
        second_context.store.backend.close()
        second_sent_store.backend.close()