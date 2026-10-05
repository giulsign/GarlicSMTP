# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import pytest
from types import SimpleNamespace

import garlicsmtp.gui.application as gui_application

from tests.support import (
    make_application_status,
)

from garlicsmtp.application import (
    MessageListViewModel,
)
from garlicsmtp.gui.application import (
    build_view_model,
)
from garlicsmtp.configuration import (
        ApplicationPaths,
        ApplicationSettings,
    )
from garlicsmtp.application import (
        ApplicationBuilder,
    )
import garlicsmtp.gui as gui

from garlicsmtp.gui.tk_main_window import (
        MainWindow as TkMainWindow,
    )
from garlicsmtp.gui.application import (
        authenticate_application,
    )
from garlicsmtp.security.auth.account_credentials import (
        AccountCredentialStore,
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
            attachment_directory_factory,
        ):
            received["window"] = self
            received["master"] = master
            received["view_model"] = (
                view_model
            )
            received["folder_opener"] = folder_opener
            received[
                "attachment_directory_factory"
            ] = attachment_directory_factory

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
        authenticate=lambda **kwargs: True,
    )

    assert received["folder_opener"] is not None
    attachment_directory_factory = (
        received[
            "attachment_directory_factory"
        ]
    )

    assert (
        attachment_directory_factory(
            "message-1"
        )
        == (
            expected_paths.cache_dir
            / "attachments"
            / "message-1"
        )
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
            attachment_directory_factory,
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
        authenticate=lambda **kwargs: True,
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
            attachment_directory_factory,
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
        authenticate=lambda **kwargs: True,
    )

    assert result == 0

    assert events == [
        "close",
        "destroy",
    ]


def test_gui_package_exports_tk_main_window():

    assert gui.MainWindow is TkMainWindow


def test_real_gui_sent_mail_persists_across_rebuild(
    tmp_path,
    monkeypatch,
):
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


def test_run_gui_authenticates_by_default_before_building_view_model(
    tmp_path,
    monkeypatch,
):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )

    events = []

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

        def destroy(
            self,
        ):
            pass

    root = FakeRoot()

    monkeypatch.setattr(
        gui_application.tk,
        "Tk",
        lambda: root,
    )

    def default_authenticate(
        *,
        paths,
        prompt,
        setup_prompt,
        invalid_credentials,
        invalid_setup,
    ):
        events.append("authenticate")
        return False

    monkeypatch.setattr(
        gui_application,
        "authenticate_application",
        default_authenticate,
    )

    def fail_if_built(
        *,
        paths=None,
    ):
        raise AssertionError(
            "build_view_model must not run "
            "before default authentication"
        )

    monkeypatch.setattr(
        gui_application,
        "build_view_model",
        fail_if_built,
    )

    result = gui_application.run_gui(
        ["garlicsmtp-gui"],
        paths=paths,
    )

    assert result == 1
    assert events == [
        "authenticate",
    ]


def test_run_gui_does_not_build_view_model_when_authentication_fails(
    tmp_path,
    monkeypatch,
):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )

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

        def destroy(
            self,
        ):
            pass

    root = FakeRoot()

    monkeypatch.setattr(
        gui_application.tk,
        "Tk",
        lambda: root,
    )

    def fail_if_built(
        *,
        paths=None,
    ):
        raise AssertionError(
            "build_view_model must not run "
            "before successful authentication"
        )

    monkeypatch.setattr(
        gui_application,
        "build_view_model",
        fail_if_built,
    )

    result = gui_application.run_gui(
        ["garlicsmtp-gui"],
        paths=paths,
        authenticate=lambda **kwargs: False,
    )

    assert result == 1


def test_run_gui_builds_view_model_after_successful_authentication(
    tmp_path,
    monkeypatch,
):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )

    events = []

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
            attachment_directory_factory,
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

    def authenticate(
        *,
        paths,
    ):
        events.append("authenticate")
        return True

    def fake_build_view_model(
        *,
        paths,
    ):
        events.append("build_view_model")
        return object()

    monkeypatch.setattr(
        gui_application,
        "build_view_model",
        fake_build_view_model,
    )

    result = gui_application.run_gui(
        ["garlicsmtp-gui"],
        paths=paths,
        authenticate=authenticate,
    )

    assert result == 0
    assert events == [
        "authenticate",
        "build_view_model",
    ]


def test_authenticate_application_accepts_existing_account(
    tmp_path,
):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )

    AccountCredentialStore(
        path=paths.account_credentials_file,
    ).create(
        username="alice",
        password="Garlic1!",
    )

    result = authenticate_application(
        paths=paths,
        prompt=lambda: (
            "alice",
            "Garlic1!",
        ),
    )

    assert result is True


def test_authenticate_application_rejects_invalid_credentials(
    tmp_path,
):

    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )

    AccountCredentialStore(
        path=paths.account_credentials_file,
    ).create(
        username="alice",
        password="Garlic1!",
    )

    credentials = iter(
        [
            (
                "alice",
                "Wrong2!",
            ),
            None,
        ]
    )

    result = authenticate_application(
        paths=paths,
        prompt=lambda: next(
            credentials
        ),
    )

    assert result is False



def test_authenticate_application_creates_account_when_missing(
    tmp_path,
):

    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )

    result = authenticate_application(
        paths=paths,
        prompt=lambda: (
            "unused",
            "Unused1!",
        ),
        setup_prompt=lambda: (
            "alice",
            "Garlic1!",
            "Garlic1!",
        ),
    )

    assert result is True
    assert paths.account_credentials_file.exists()

    assert AccountCredentialStore(
        path=paths.account_credentials_file,
    ).authenticate(
        username="alice",
        password="Garlic1!",
    ) is True


def test_authenticate_application_rejects_cancelled_account_setup(
    tmp_path,
):

    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )

    result = authenticate_application(
        paths=paths,
        prompt=lambda: (
            "unused",
            "Unused1!",
        ),
        setup_prompt=lambda: None,
    )

    assert result is False
    assert not paths.account_credentials_file.exists()


def test_authenticate_application_rejects_mismatched_setup_passwords(
    tmp_path,
):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )

    credentials = iter(
        [
            (
                "alice",
                "Garlic1!",
                "Different2!",
            ),
            None,
        ]
    )

    result = authenticate_application(
        paths=paths,
        prompt=lambda: (
            "unused",
            "Unused1!",
        ),
        setup_prompt=lambda: next(
            credentials
        ),
    )

    assert result is False
    assert not paths.account_credentials_file.exists()


def test_authenticate_application_returns_false_when_login_is_cancelled(
    tmp_path,
):

    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )

    AccountCredentialStore(
        path=paths.account_credentials_file,
    ).create(
        username="alice",
        password="Garlic1!",
    )

    result = authenticate_application(
        paths=paths,
        prompt=lambda: None,
    )

    assert result is False


def test_run_gui_default_authentication_wires_login_prompt_to_root(
    tmp_path,
    monkeypatch,
):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )

    events = []

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

        def destroy(
            self,
        ):
            pass

    root = FakeRoot()

    monkeypatch.setattr(
        gui_application.tk,
        "Tk",
        lambda: root,
    )

    def fake_prompt_login(
        master,
    ):
        events.append(
            ("login_prompt", master)
        )
        return (
            "alice",
            "Garlic1!",
        )

    monkeypatch.setattr(
        gui_application,
        "prompt_login",
        fake_prompt_login,
    )

    def fake_authenticate_application(
        *,
        paths,
        prompt,
        setup_prompt,
        invalid_credentials,
        invalid_setup,
    ):
        events.append(
            ("authenticate", paths)
        )
        credentials = prompt()
        events.append(
            ("credentials", credentials)
        )
        return False

    monkeypatch.setattr(
        gui_application,
        "authenticate_application",
        fake_authenticate_application,
    )

    monkeypatch.setattr(
        gui_application,
        "build_view_model",
        lambda **kwargs: (
            pytest.fail(
                "build_view_model must not run"
            )
        ),
    )

    result = gui_application.run_gui(
        ["garlicsmtp-gui"],
        paths=paths,
    )

    assert result == 1
    assert events == [
        ("authenticate", paths),
        ("login_prompt", root),
        (
            "credentials",
            (
                "alice",
                "Garlic1!",
            ),
        ),
    ]


def test_run_gui_default_authentication_wires_setup_prompt_to_root(
    tmp_path,
    monkeypatch,
):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )

    events = []

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

        def destroy(
            self,
        ):
            pass

    root = FakeRoot()

    monkeypatch.setattr(
        gui_application.tk,
        "Tk",
        lambda: root,
    )

    def fake_prompt_setup(
        master,
    ):
        events.append(
            ("setup_prompt", master)
        )
        return (
            "alice",
            "Garlic1!",
            "Garlic1!",
        )

    monkeypatch.setattr(
        gui_application,
        "prompt_setup",
        fake_prompt_setup,
    )

    def fake_authenticate_application(
        *,
        paths,
        prompt,
        setup_prompt,
        invalid_credentials,
        invalid_setup,
    ):
        events.append(
            ("authenticate", paths)
        )
        credentials = setup_prompt()
        events.append(
            ("credentials", credentials)
        )
        return False

    monkeypatch.setattr(
        gui_application,
        "authenticate_application",
        fake_authenticate_application,
    )

    monkeypatch.setattr(
        gui_application,
        "build_view_model",
        lambda **kwargs: (
            pytest.fail(
                "build_view_model must not run"
            )
        ),
    )

    result = gui_application.run_gui(
        ["garlicsmtp-gui"],
        paths=paths,
    )

    assert result == 1
    assert events == [
        ("authenticate", paths),
        ("setup_prompt", root),
        (
            "credentials",
            (
                "alice",
                "Garlic1!",
                "Garlic1!",
            ),
        ),
    ]


def test_authenticate_application_retries_after_invalid_credentials(
    tmp_path,
):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )

    AccountCredentialStore(
        path=paths.account_credentials_file,
    ).create(
        username="alice",
        password="Garlic1!",
    )

    credentials = iter(
        [
            (
                "alice",
                "Wrong2!",
            ),
            (
                "alice",
                "Garlic1!",
            ),
        ]
    )

    result = authenticate_application(
        paths=paths,
        prompt=lambda: next(
            credentials
        ),
    )

    assert result is True


def test_authenticate_application_reports_invalid_credentials_before_retry(
    tmp_path,
):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )

    AccountCredentialStore(
        path=paths.account_credentials_file,
    ).create(
        username="alice",
        password="Garlic1!",
    )

    events = []

    credentials = iter(
        [
            (
                "alice",
                "Wrong2!",
            ),
            None,
        ]
    )

    def prompt():
        credentials_value = next(
            credentials
        )
        events.append(
            ("prompt", credentials_value)
        )
        return credentials_value

    def invalid_credentials():
        events.append(
            ("invalid",)
        )

    result = authenticate_application(
        paths=paths,
        prompt=prompt,
        invalid_credentials=invalid_credentials,
    )

    assert result is False

    assert events == [
        (
            "prompt",
            (
                "alice",
                "Wrong2!",
            ),
        ),
        ("invalid",),
        ("prompt", None),
    ]


def test_run_gui_default_authentication_shows_generic_invalid_credentials_error(
    tmp_path,
    monkeypatch,
):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )

    dialogs = []

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

        def destroy(
            self,
        ):
            pass

    root = FakeRoot()

    monkeypatch.setattr(
        gui_application.tk,
        "Tk",
        lambda: root,
    )

    def fake_authenticate_application(
        *,
        paths,
        prompt,
        setup_prompt,
        invalid_credentials,
        invalid_setup,
    ):
        invalid_credentials()
        return False

    monkeypatch.setattr(
        gui_application,
        "authenticate_application",
        fake_authenticate_application,
    )

    monkeypatch.setattr(
        gui_application.messagebox,
        "showerror",
        lambda title, message, **kwargs: (
            dialogs.append(
                (
                    title,
                    message,
                    kwargs,
                )
            )
        ),
    )

    result = gui_application.run_gui(
        ["garlicsmtp-gui"],
        paths=paths,
    )

    assert result == 1

    assert dialogs == [
        (
            "GarlicSMTP login",
            "Invalid username or password",
            {
                "parent": root,
            },
        ),
    ]


def test_run_gui_default_authentication_shows_invalid_setup_error(
    tmp_path,
    monkeypatch,
):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )

    dialogs = []

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

        def destroy(
            self,
        ):
            pass

    root = FakeRoot()

    monkeypatch.setattr(
        gui_application.tk,
        "Tk",
        lambda: root,
    )

    def fake_authenticate_application(
        *,
        paths,
        prompt,
        setup_prompt,
        invalid_credentials,
        invalid_setup,
    ):
        invalid_setup(
            "Account password must contain an uppercase letter"
        )
        return False

    monkeypatch.setattr(
        gui_application,
        "authenticate_application",
        fake_authenticate_application,
    )

    monkeypatch.setattr(
        gui_application.messagebox,
        "showerror",
        lambda title, message, **kwargs: (
            dialogs.append(
                (
                    title,
                    message,
                    kwargs,
                )
            )
        ),
    )

    result = gui_application.run_gui(
        ["garlicsmtp-gui"],
        paths=paths,
    )

    assert result == 1

    assert dialogs == [
        (
            "GarlicSMTP account setup",
            "Account password must contain an uppercase letter",
            {
                "parent": root,
            },
        ),
    ]


def test_authenticate_application_retries_setup_after_password_mismatch(
    tmp_path,
):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )

    credentials = iter(
        [
            (
                "alice",
                "Garlic1!",
                "Different2!",
            ),
            (
                "alice",
                "Garlic1!",
                "Garlic1!",
            ),
        ]
    )

    result = authenticate_application(
        paths=paths,
        prompt=lambda: None,
        setup_prompt=lambda: next(
            credentials
        ),
    )

    assert result is True

    assert paths.account_credentials_file.exists()


def test_authenticate_application_retries_setup_after_invalid_credentials(
    tmp_path,
):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )

    credentials = iter(
        [
            (
                "alice",
                "garlic1!",
                "garlic1!",
            ),
            (
                "alice",
                "Garlic1!",
                "Garlic1!",
            ),
        ]
    )

    result = authenticate_application(
        paths=paths,
        prompt=lambda: None,
        setup_prompt=lambda: next(
            credentials
        ),
    )

    assert result is True
    assert paths.account_credentials_file.exists()


def test_authenticate_application_reports_invalid_setup_before_retry(
    tmp_path,
):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )

    events = []

    credentials = iter(
        [
            (
                "alice",
                "garlic1!",
                "garlic1!",
            ),
            None,
        ]
    )

    def setup_prompt():
        credentials_value = next(
            credentials
        )
        events.append(
            ("prompt", credentials_value)
        )
        return credentials_value

    def invalid_setup(message):
        events.append(
            ("invalid", message)
        )

    result = authenticate_application(
        paths=paths,
        prompt=lambda: None,
        setup_prompt=setup_prompt,
        invalid_setup=invalid_setup,
    )

    assert result is False

    assert events == [
        (
            "prompt",
            (
                "alice",
                "garlic1!",
                "garlic1!",
            ),
        ),
        (
            "invalid",
            "Account password must contain an uppercase letter",
        ),
        ("prompt", None),
    ]

    assert not paths.account_credentials_file.exists()


def test_authenticate_application_reports_password_mismatch_before_retry(
    tmp_path,
):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )

    events = []

    credentials = iter(
        [
            (
                "alice",
                "Garlic1!",
                "Different2!",
            ),
            None,
        ]
    )

    def setup_prompt():
        credentials_value = next(
            credentials
        )
        events.append(
            ("prompt", credentials_value)
        )
        return credentials_value

    def invalid_setup(message):
        events.append(
            ("invalid", message)
        )

    result = authenticate_application(
        paths=paths,
        prompt=lambda: None,
        setup_prompt=setup_prompt,
        invalid_setup=invalid_setup,
    )

    assert result is False

    assert events == [
        (
            "prompt",
            (
                "alice",
                "Garlic1!",
                "Different2!",
            ),
        ),
        (
            "invalid",
            "Passwords do not match",
        ),
        ("prompt", None),
    ]

    assert not paths.account_credentials_file.exists()