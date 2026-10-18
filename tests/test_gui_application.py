# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import pytest
from types import SimpleNamespace
from pathlib import Path
import json

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
from sqlcipher3 import dbapi2 as sqlcipher

from garlicsmtp.models import (
        Envelope,
        MailHeaders,
        MailMessage,
    )
from garlicsmtp.storage.sqlite.backend import (
        SQLiteMessageStoreBackend,
    )
from garlicsmtp.storage.attachment_store import (
        AttachmentStore,
    )


@pytest.fixture(
    autouse=True,
)
def stub_run_gui_application_fonts(
    request,
    monkeypatch,
):
    if request.node.name.startswith(
        "test_run_gui_"
    ):
        monkeypatch.setattr(
            gui_application,
            "configure_application_fonts",
            lambda root: None,
        )


def test_gui_builds_message_list_view_model(
    tmp_path,
    monkeypatch,
    dek,
):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )
    view_model = build_view_model(
        paths=paths,
        dek=dek,
    )

    assert isinstance(
        view_model.message_list,
        MessageListViewModel,
    )


def test_gui_builds_received_and_sent_message_view_models(dek, tmp_path):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )
    view_model = build_view_model(
        paths=paths,
        dek=dek,
    )

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
    dek,
):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )

    settings = ApplicationSettings()
    settings.tor.enabled = False

    real_builder = ApplicationBuilder(
        paths=paths,
        settings=settings,
        dek=dek,
    )

    class TestBuilder:

        def __init__(
            self,
            *,
            paths,
            dek,
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
        gui_application.build_view_model(dek=dek)
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
    dek,
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
            dek,
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
        gui_application.build_view_model(dek=dek)
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
    dek,
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
            dek,
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
        gui_application.build_view_model(dek=dek)
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
    dek,
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
            dek,
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
        gui_application.build_view_model(dek=dek)
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
    dek,
):

    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )

    settings = ApplicationSettings()
    settings.tor.enabled = False

    real_builder = ApplicationBuilder(
        paths=paths,
        settings=settings,
        dek=dek,
    )

    class TestBuilder:

        def __init__(
            self,
            *,
            paths,
            dek,
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
        gui_application.build_view_model(dek=dek)
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
    dek,
):

    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )

    settings = ApplicationSettings()
    settings.tor.enabled = False

    real_builder = ApplicationBuilder(
        paths=paths,
        settings=settings,
        dek=dek,
    )

    class TestBuilder:

        def __init__(
            self,
            *,
            paths,
            dek,
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
        gui_application.build_view_model(dek=dek)
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


def test_configure_application_fonts_increases_named_fonts(
    monkeypatch,
):
    configured = []
    received_roots = []

    class FakeFont:

        def __init__(
            self,
            name,
        ):
            self.name = name

        def cget(
            self,
            option,
        ):
            assert option == "size"
            return 10

        def configure(
            self,
            *,
            size,
        ):
            configured.append(
                (self.name, size)
            )

    expected_root = object()

    def fake_nametofont(
        name,
        *,
        root,
    ):
        received_roots.append(root)
        return FakeFont(name)

    monkeypatch.setattr(
        gui_application.tkfont,
        "nametofont",
        fake_nametofont,
    )

    gui_application.configure_application_fonts(
        expected_root,
    )

    assert received_roots == [
        expected_root,
        expected_root,
        expected_root,
        expected_root,
        expected_root,
    ]

    assert configured == [
        ("TkDefaultFont", 12),
        ("TkTextFont", 12),
        ("TkFixedFont", 12),
        ("TkMenuFont", 12),
        ("TkHeadingFont", 12),
    ]


def test_run_gui_sets_application_icon(
    monkeypatch,
    dek,
):
    icon_calls = []

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

        def iconphoto(
            self,
            default,
            image,
        ):
            icon_calls.append(
                (default, image)
            )

        def withdraw(
            self,
        ):
            pass

        def deiconify(
            self,
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

    icon = object()

    monkeypatch.setattr(
        gui_application.tk,
        "Tk",
        FakeRoot,
    )

    loaded_files = []

    def fake_photo_image(
        **kwargs,
    ):
        loaded_files.append(
            kwargs["file"]
        )
        return icon

    monkeypatch.setattr(
        gui_application.tk,
        "PhotoImage",
        fake_photo_image,
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

    class FakePaths:
        application_icon = Path(
            "/application/garlicsmtp.png"
        )

    result = gui_application.run_gui(
        ["garlicsmtp-gui"],
        paths=FakePaths(),
        authenticate=lambda **kwargs: dek,
    )

    assert result == 0
    assert loaded_files == [
        str(
            Path(
                "/application"
            )
            / "garlicsmtp.png"
        ),
    ]
    assert icon_calls == [
        (True, icon),
    ]


def test_run_gui_hides_root_until_authentication_succeeds(
    monkeypatch,
    dek,
):
    events = []

    class FakePaths:
        application_icon = Path(
            "/application/garlicsmtp.png"
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

        def withdraw(
            self,
        ):
            events.append("withdraw")

        def deiconify(
            self,
        ):
            events.append("deiconify")

        def protocol(
            self,
            name,
            callback,
        ):
            pass

        def mainloop(
            self,
        ):
            events.append("mainloop")

        def iconphoto(
            self,
            default,
            image,
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
            events.append("window")

        def pack(
            self,
            **kwargs,
        ):
            pass

        def close(
            self,
        ):
            pass

    def authenticate(
        **kwargs,
    ):
        events.append("authenticate")
        return dek

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

    monkeypatch.setattr(
        gui_application.tk,
        "PhotoImage",
        lambda **kwargs: object(),
    )

    result = gui_application.run_gui(
        ["garlicsmtp-gui"],
        paths=FakePaths(),
        authenticate=authenticate,
    )

    assert result == 0
    assert events == [
        "withdraw",
        "authenticate",
        "deiconify",
        "window",
        "mainloop",
    ]


def test_run_gui_uses_user_application_paths(
    tmp_path,
    monkeypatch,
    dek,
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

        def withdraw(
            self,
        ):
            pass

        def deiconify(
            self,
        ):
            pass

        def iconphoto(
            self,
            default,
            image,
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
        dek:bytes,
    ):
        received["paths"] = paths
        received["dek"] = dek
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

    monkeypatch.setattr(
        gui_application.tk,
        "PhotoImage",
        lambda **kwargs: object(),
    )

    result = gui_application.run_gui(
        ["garlicsmtp-gui"],
        authenticate=lambda **kwargs: dek,
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
    assert received["dek"] == dek

    assert (
        received["title"]
        == "GarlicSMTP Monitor"
    )

    assert received["mainloop"] is True

    assert (
        received["protocol"][0]
        == "WM_DELETE_WINDOW"
    )


def test_run_gui_does_not_destroy_root_when_close_is_refused(
    tmp_path,
    monkeypatch,
    dek,
):
    paths = ApplicationPaths.for_development(
        project_root=tmp_path,
        home=tmp_path,
    )

    received = {
        "destroy_calls": 0,
        "close_calls": 0,
        "warnings": [],
    }

    class FakeRoot:
        def title(self, value):
            pass

        def geometry(self, value):
            pass

        def withdraw(self):
            pass

        def deiconify(self):
            pass

        def iconphoto(self, default, image):
            pass

        def protocol(self, name, callback):
            received["protocol_name"] = name
            received["close_callback"] = callback

        def mainloop(self):
            received["close_callback"]()

        def destroy(self):
            received["destroy_calls"] += 1

    class FakeWindow:
        def __init__(self, master, view_model, **kwargs):
            pass

        def pack(self, **kwargs):
            pass

        def close(self):
            received["close_calls"] += 1
            return False

    monkeypatch.setattr(
        gui_application.tk,
        "Tk",
        FakeRoot,
    )

    monkeypatch.setattr(
        gui_application.tk,
        "PhotoImage",
        lambda **kwargs: object(),
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

    monkeypatch.setattr(
        gui_application.messagebox,
        "showwarning",
        lambda title, message, **kwargs: (
            received["warnings"].append(
                (title, message)
            )
        ),
    )

    result = gui_application.run_gui(
        ["garlicsmtp-gui"],
        paths=paths,
        authenticate=lambda **kwargs: dek,
    )

    assert result == 0
    assert received["protocol_name"] == "WM_DELETE_WINDOW"
    assert received["close_calls"] == 1
    assert received["destroy_calls"] == 0

    assert len(received["warnings"]) == 1
    assert received["warnings"][0][0] == "GarlicSMTP"
    assert "message is being sent" in (
        received["warnings"][0][1].lower()
    )


def test_run_gui_uses_provided_application_paths(
    tmp_path,
    monkeypatch,
    dek,
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

        def withdraw(
            self,
        ):
            pass

        def deiconify(
            self,
        ):
            pass

        def iconphoto(
            self,
            default,
            image,
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
        dek: bytes,
    ):
        received["paths"] = paths
        received["dek"] = dek
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

    monkeypatch.setattr(
        gui_application.tk,
        "PhotoImage",
        lambda **kwargs: object(),
    )

    result = gui_application.run_gui(
        ["garlicsmtp-gui"],
        paths=expected_paths,
        authenticate=lambda **kwargs: dek,
    )

    assert result == 0
    assert received["paths"] == expected_paths
    assert received["dek"] == dek


def test_build_view_model_uses_provided_application_paths(
    tmp_path,
    monkeypatch,
    dek,
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
            dek,
        ):
            received["paths"] = paths
            received["dek"] = dek

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
        paths=expected_paths, dek=dek,
    )

    assert received["paths"] == expected_paths
    assert received["dek"] == dek


def test_run_gui_closes_window_before_destroying_root(
    monkeypatch,
    dek,
):
    events = []
    received = {}

    class FakePaths:
        application_icon = Path(
            "/application/garlicsmtp.png"
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

        def withdraw(
            self,
        ):
            pass

        def deiconify(
            self,
        ):
            pass

        def iconphoto(
            self,
            default,
            image,
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
            events.append("close")
            return True

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

    monkeypatch.setattr(
        gui_application.tk,
        "PhotoImage",
        lambda **kwargs: object(),
    )

    result = gui_application.run_gui(
        ["garlicsmtp-gui"],
        paths=FakePaths(),
        authenticate=lambda **kwargs: dek,
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
    dek,
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
            dek,
        ):
            self.builder = ApplicationBuilder(
                paths=paths,
                settings=settings,
                dek=dek,
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
            paths=paths, dek=dek,
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
            paths=paths, dek=dek,
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

        def withdraw(
            self,
        ):
            pass

        def iconphoto(
            self,
            default,
            image,
        ):
            pass

    root = FakeRoot()

    monkeypatch.setattr(
        gui_application.tk,
        "Tk",
        lambda: root,
    )

    def fake_prompt_setup(master):
        assert master is root
        events.append("setup_cancelled")
        return None

    monkeypatch.setattr(
        gui_application,
        "prompt_setup",
        fake_prompt_setup,
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

    monkeypatch.setattr(
        gui_application.tk,
        "PhotoImage",
        lambda **kwargs: object(),
    )

    result = gui_application.run_gui(
        ["garlicsmtp-gui"],
        paths=paths,
    )

    assert result == 1
    assert events == ["setup_cancelled"]
    assert not paths.account_credentials_file.exists()


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

        def withdraw(
            self,
        ):
            pass

        def iconphoto(
            self,
            default,
            image,
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

    monkeypatch.setattr(
        gui_application.tk,
        "PhotoImage",
        lambda **kwargs: object(),
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
    dek = bytes(range(32))
    expected_paths = paths
    expected_dek = dek

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

        def withdraw(
            self,
        ):
            pass

        def deiconify(
            self,
        ):
            pass

        def iconphoto(
            self,
            default,
            image,
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
        return dek


    def fake_build_view_model(
        *,
        paths,
        dek,
    ):
        assert paths == expected_paths
        assert dek == expected_dek
        events.append("build_view_model")
        return object()


    monkeypatch.setattr(
        gui_application,
        "build_view_model",
        fake_build_view_model,
    )

    monkeypatch.setattr(
        gui_application.tk,
        "PhotoImage",
        lambda **kwargs: object(),
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

    store = AccountCredentialStore(
        path=paths.account_credentials_file,
    )
    store.create(
        username="alice",
        password="Garlic1!",
    )
    store.enable_recovery(
        username="alice",
        password="Garlic1!",
        recovery_key="test-recovery-key",
    )
    store.confirm_recovery(username="alice", recovery_key="test-recovery-key")

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

        def withdraw(
            self,
        ):
            pass

        def iconphoto(
            self,
            default,
            image,
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

    def fake_unlock_application_dek(
        *,
        paths,
        prompt,
        invalid_credentials=None,
        show_recovery=None,
        on_forgot_password=None,
    ):
        events.append(("unlock", paths))
        credentials = prompt()
        events.append(("credentials", credentials))
        return None

    monkeypatch.setattr(
        gui_application,
        "unlock_application_dek",
        fake_unlock_application_dek,
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

    monkeypatch.setattr(
        gui_application.tk,
        "PhotoImage",
        lambda **kwargs: object(),
    )

    result = gui_application.run_gui(
        ["garlicsmtp-gui"],
        paths=paths,
    )

    assert result == 1
    assert events == [
        ("unlock", paths),
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

        def withdraw(
            self,
        ):
            pass

        def iconphoto(
            self,
            default,
            image,
        ):
            pass

    root = FakeRoot()

    monkeypatch.setattr(
        gui_application.tk,
        "Tk",
        lambda: root,
    )

    def fake_prompt_setup(master):
        events.append(("setup_prompt", master))
        return None

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
        "build_view_model",
        lambda **kwargs: (
            pytest.fail(
                "build_view_model must not run"
            )
        ),
    )

    monkeypatch.setattr(
        gui_application.tk,
        "PhotoImage",
        lambda **kwargs: object(),
    )

    result = gui_application.run_gui(
        ["garlicsmtp-gui"],
        paths=paths,
    )

    assert result == 1
    assert result == 1
    assert events == [
        ("setup_prompt", root),
    ]
    assert not paths.account_credentials_file.exists()


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

    store = AccountCredentialStore(
        path=paths.account_credentials_file,
    )
    store.create(
        username="alice",
        password="Garlic1!",
    )
    store.enable_recovery(
        username="alice",
        password="Garlic1!",
        recovery_key="test-recovery-key",
    )
    store.confirm_recovery(username="alice", recovery_key="test-recovery-key")

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

        def withdraw(
            self,
        ):
            pass

        def iconphoto(
            self,
            default,
            image,
        ):
            pass

    root = FakeRoot()

    monkeypatch.setattr(
        gui_application.tk,
        "Tk",
        lambda: root,
    )

    credentials = iter([
        ("alice", "Wrong2!"),
        None,
    ])

    monkeypatch.setattr(
        gui_application,
        "prompt_login",
        lambda master: next(credentials),
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

    monkeypatch.setattr(
        gui_application.tk,
        "PhotoImage",
        lambda **kwargs: object(),
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

        def withdraw(
            self,
        ):
            pass

        def iconphoto(
            self,
            default,
            image,
        ):
            pass

    root = FakeRoot()

    monkeypatch.setattr(
        gui_application.tk,
        "Tk",
        lambda: root,
    )

    credentials = iter([
        ("alice", "garlic1!", "garlic1!"),
        None,
    ])

    monkeypatch.setattr(
        gui_application,
        "prompt_setup",
        lambda master: next(credentials),
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

    monkeypatch.setattr(
        gui_application.tk,
        "PhotoImage",
        lambda **kwargs: object(),
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

    assert not paths.account_credentials_file.exists()


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


def test_gui_unlocks_dek_for_existing_account(
    tmp_path,
):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )

    store = AccountCredentialStore(
        path=paths.account_credentials_file,
    )
    store.create(
        username="alice",
        password="Garlic1!",
    )
    store.enable_recovery(
        username="alice",
        password="Garlic1!",
        recovery_key="test-recovery-key",
    )

    store.confirm_recovery(username="alice", recovery_key="test-recovery-key")

    result = gui_application.unlock_application_dek(
        paths=paths,
        prompt=lambda: ("alice", "Garlic1!"),
    )

    expected_dek = store.unlock_dek_with_password(
        username="alice",
        password="Garlic1!",
    )

    assert result == expected_dek
    assert isinstance(result, bytes)
    assert len(result) == 32


def test_gui_unlock_retries_after_invalid_password(
    tmp_path,
):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )

    store = AccountCredentialStore(
        path=paths.account_credentials_file,
    )
    store.create(
        username="alice",
        password="Garlic1!",
    )
    store.enable_recovery(
        username="alice",
        password="Garlic1!",
        recovery_key="test-recovery-key",
    )

    store.confirm_recovery(username="alice", recovery_key="test-recovery-key")

    attempts = iter([
        ("alice", "Wrong2!"),
        ("alice", "Garlic1!"),
    ])

    result = gui_application.unlock_application_dek(
        paths=paths,
        prompt=lambda: next(attempts),
    )

    assert result == store.unlock_dek_with_password(
        username="alice",
        password="Garlic1!",
    )


def test_gui_unlock_returns_none_when_cancelled(
    tmp_path,
):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )

    result = gui_application.unlock_application_dek(
        paths=paths,
        prompt=lambda: None,
    )

    assert result is None


def test_gui_unlock_rejects_account_without_dek(
    tmp_path,
):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )

    store = AccountCredentialStore(
        path=paths.account_credentials_file,
    )
    store.create(
        username="alice",
        password="Garlic1!",
    )

    prompts = iter([
        ("alice", "Garlic1!"),
    ])

    with pytest.raises(
        ValueError,
        match="DEK",
    ):
        gui_application.unlock_application_dek(
            paths=paths,
            prompt=lambda: next(prompts),
        )


def test_gui_setup_creates_recoverable_dek(
    tmp_path,
):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )

    displayed_recovery_keys = []

    dek = gui_application.setup_application_dek(
        paths=paths,
        username="alice",
        password="Garlic1!",
        show_recovery=lambda recovery_key: (
            displayed_recovery_keys.append(recovery_key),
            recovery_key,
        )[1],
    )

    assert isinstance(dek, bytes)
    assert len(dek) == 32

    assert len(displayed_recovery_keys) == 1

    recovery_key = displayed_recovery_keys[0]

    assert isinstance(recovery_key, str)
    assert len(recovery_key) == 64

    store = AccountCredentialStore(
        path=paths.account_credentials_file,
    )

    credentials = json.loads(
        paths.account_credentials_file.read_text(
            encoding="utf-8",
        )
    )

    assert credentials["recovery_confirmed"] is True


    assert store.unlock_dek_with_password(
        username="alice",
        password="Garlic1!",
    ) == dek

    assert store.unlock_dek_with_recovery(
        username="alice",
        recovery_key=recovery_key,
    ) == dek

    assert recovery_key not in (
        paths.account_credentials_file.read_text(
            encoding="utf-8",
        )
    )


def test_gui_setup_requires_recovery_confirmation(
    tmp_path,
):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )

    displayed_recovery_keys = []

    def show_recovery(recovery_key):
        displayed_recovery_keys.append(recovery_key)
        return False

    with pytest.raises(
        ValueError,
        match="recovery",
    ):
        gui_application.setup_application_dek(
            paths=paths,
            username="alice",
            password="Garlic1!",
            show_recovery=show_recovery,
        )

    assert len(displayed_recovery_keys) == 1

    store = AccountCredentialStore(
        path=paths.account_credentials_file,
    )

    assert store.unlock_dek_with_recovery(
        username="alice",
        recovery_key=displayed_recovery_keys[0],
    ) == store.unlock_dek_with_password(
        username="alice",
        password="Garlic1!",
    )

    credentials = json.loads(
        paths.account_credentials_file.read_text(
            encoding="utf-8",
        )
    )
    assert credentials["recovery_confirmed"] is False


def test_gui_unlock_rejects_unconfirmed_recovery(tmp_path):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )

    store = AccountCredentialStore(
        path=paths.account_credentials_file,
    )
    store.create(
        username="alice",
        password="Garlic1!",
    )
    store.enable_recovery(
        username="alice",
        password="Garlic1!",
        recovery_key="test-recovery-key",
    )

    with pytest.raises(
        ValueError,
        match="recovery",
    ):
        gui_application.unlock_application_dek(
            paths=paths,
            prompt=lambda: ("alice", "Garlic1!"),
        )



def test_build_view_model_passes_dek_to_both_databases(
    tmp_path,
    monkeypatch,
):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )
    dek = bytes(range(32))
    received = {}

    class FakeBuilder:
        def __init__(self, *, paths, dek):
            received["builder_paths"] = paths
            received["builder_dek"] = dek

        def build(self):
            return SimpleNamespace(
                pipeline=FakePipeline(),
                store=object(),
                signer=None,
                paths=paths,
            )

    class FakeSQLiteBackend:
        def __init__(self, path, *, dek):
            received["sent_path"] = path
            received["sent_dek"] = dek

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
    monkeypatch.setattr(
        gui_application,
        "SQLiteMessageStoreBackend",
        FakeSQLiteBackend,
    )

    gui_application.build_view_model(
        paths=paths,
        dek=dek,
    )

    assert received["builder_paths"] == paths
    assert received["builder_dek"] == dek
    assert received["sent_path"] == paths.sent_mailbox_database
    assert received["sent_dek"] == dek



def test_run_gui_default_login_unlocks_dek_before_build(
    tmp_path,
    monkeypatch,
    dek,
):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )

    store = AccountCredentialStore(
        path=paths.account_credentials_file,
    )
    store.create(
        username="alice",
        password="Garlic1!",
    )
    store.enable_recovery(
        username="alice",
        password="Garlic1!",
        recovery_key="test-recovery-key",
    )
    store.confirm_recovery(username="alice", recovery_key="test-recovery-key")

    expected_dek = store.unlock_dek_with_password(
        username="alice",
        password="Garlic1!",
    )

    events = []

    class FakeRoot:
        def title(self, value):
            pass

        def geometry(self, value):
            pass

        def withdraw(self):
            events.append("withdraw")

        def deiconify(self):
            events.append("deiconify")

        def iconphoto(self, default, image):
            pass

        def protocol(self, name, callback):
            pass

        def mainloop(self):
            pass

        def destroy(self):
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
            events.append("window")

        def pack(self, **kwargs):
            pass

        def close(self):
            pass

    monkeypatch.setattr(
        gui_application.tk,
        "Tk",
        FakeRoot,
    )
    monkeypatch.setattr(
        gui_application.tk,
        "PhotoImage",
        lambda **kwargs: object(),
    )
    monkeypatch.setattr(
        gui_application,
        "MainWindow",
        FakeWindow,
    )

    def fake_prompt_login(root):
        events.append("login")
        return ("alice", "Garlic1!")

    monkeypatch.setattr(
        gui_application,
        "prompt_login",
        fake_prompt_login,
    )

    def fake_build_view_model(*, paths, dek):
        assert dek == expected_dek
        events.append("build")
        return object()

    monkeypatch.setattr(
        gui_application,
        "build_view_model",
        fake_build_view_model,
    )

    result = gui_application.run_gui(
        paths=paths,
    )

    assert events == [
        "withdraw",
        "login",
        "build",
        "deiconify",
        "window",
    ]



def test_run_gui_first_setup_creates_dek_and_confirms_recovery(
    tmp_path,
    monkeypatch,
):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )
    events = []
    recovery_keys = []

    class FakeRoot:
        def title(self, value):
            pass

        def geometry(self, value):
            pass

        def withdraw(self):
            events.append("withdraw")

        def deiconify(self):
            events.append("deiconify")

        def iconphoto(self, default, image):
            pass

        def protocol(self, name, callback):
            pass

        def mainloop(self):
            pass

        def destroy(self):
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
            events.append("window")

        def pack(self, **kwargs):
            pass

        def close(self):
            pass

    monkeypatch.setattr(
        gui_application.tk,
        "Tk",
        FakeRoot,
    )
    monkeypatch.setattr(
        gui_application.tk,
        "PhotoImage",
        lambda **kwargs: object(),
    )
    monkeypatch.setattr(
        gui_application,
        "MainWindow",
        FakeWindow,
    )

    def fake_prompt_setup(root):
        events.append("setup")
        return ("alice", "Garlic1!", "Garlic1!")

    monkeypatch.setattr(
        gui_application,
        "prompt_setup",
        fake_prompt_setup,
    )

    def fake_show_recovery(recovery_key, *, master):
        events.append("recovery")
        recovery_keys.append(recovery_key)
        assert isinstance(master, FakeRoot)
        return recovery_key

    monkeypatch.setattr(
        gui_application,
        "show_recovery_key",
        fake_show_recovery,
        raising=False,
    )

    def fake_build_view_model(*, paths, dek):
        store = AccountCredentialStore(
            path=paths.account_credentials_file,
        )
        assert dek == store.unlock_dek_with_password(
            username="alice",
            password="Garlic1!",
        )
        events.append("build")
        return object()

    monkeypatch.setattr(
        gui_application,
        "build_view_model",
        fake_build_view_model,
    )

    result = gui_application.run_gui(paths=paths)

    assert result == 0
    assert len(recovery_keys) == 1
    assert len(recovery_keys[0]) == 64

    store = AccountCredentialStore(
        path=paths.account_credentials_file,
    )
    assert store.unlock_dek_with_recovery(
        username="alice",
        recovery_key=recovery_keys[0],
    ) == store.unlock_dek_with_password(
        username="alice",
        password="Garlic1!",
    )

    assert events == [
        "withdraw",
        "setup",
        "recovery",
        "build",
        "deiconify",
        "window",
    ]


def test_show_recovery_key_uses_confirmation_dialog(monkeypatch):
    events = []

    class FakeRecoveryDialog:
        def __init__(self, master, recovery_key):
            events.append(("create", master, recovery_key))
            self.result = True

        def grab_set(self):
            events.append("grab")

        def wait_window(self):
            events.append("wait")

    root = object()

    monkeypatch.setattr(
        gui_application,
        "RecoveryDialog",
        FakeRecoveryDialog,
        raising=False,
    )

    result = gui_application.show_recovery_key(
        "test-recovery-key",
        master=root,
    )

    assert result is True
    assert events == [
        ("create", root, "test-recovery-key"),
        "grab",
        "wait",
    ]


def test_gui_unlock_can_resume_unconfirmed_recovery(tmp_path):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )

    store = AccountCredentialStore(
        path=paths.account_credentials_file,
    )
    store.create(
        username="alice",
        password="Garlic1!",
    )
    store.enable_recovery(
        username="alice",
        password="Garlic1!",
        recovery_key="old-recovery-key",
    )

    original_dek = store.unlock_dek_with_password(
        username="alice",
        password="Garlic1!",
    )

    displayed_keys = []

    result = gui_application.unlock_application_dek(
        paths=paths,
        prompt=lambda: ("alice", "Garlic1!"),
        show_recovery=lambda key: (
            displayed_keys.append(key),
            key,
        )[1],
    )

    assert result == original_dek
    assert len(displayed_keys) == 1
    assert len(displayed_keys[0]) == 64

    assert store.unlock_dek_with_recovery(
        username="alice",
        recovery_key=displayed_keys[0],
    ) == original_dek

    assert store._read_credentials()["recovery_confirmed"] is True


def test_gui_resume_recovery_cancel_keeps_account_unconfirmed(tmp_path):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )

    store = AccountCredentialStore(
        path=paths.account_credentials_file,
    )
    store.create(
        username="alice",
        password="Garlic1!",
    )
    store.enable_recovery(
        username="alice",
        password="Garlic1!",
        recovery_key="old-recovery-key",
    )

    original_dek = store.unlock_dek_with_password(
        username="alice",
        password="Garlic1!",
    )

    displayed_keys = []

    def show_recovery(recovery_key):
        displayed_keys.append(recovery_key)
        return False

    with pytest.raises(ValueError, match="recovery"):
        gui_application.unlock_application_dek(
            paths=paths,
            prompt=lambda: ("alice", "Garlic1!"),
            show_recovery=show_recovery,
        )

    assert len(displayed_keys) == 1

    assert store._read_credentials()["recovery_confirmed"] is False

    assert store.unlock_dek_with_password(
        username="alice",
        password="Garlic1!",
    ) == original_dek

    assert store.unlock_dek_with_recovery(
        username="alice",
        recovery_key=displayed_keys[0],
    ) == original_dek


def test_run_gui_passes_recovery_dialog_to_unlock(
    tmp_path,
    monkeypatch,
):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )

    paths.account_credentials_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    paths.account_credentials_file.touch()

    class FakeRoot:
        def title(self, value):
            pass

        def geometry(self, value):
            pass

        def withdraw(self):
            pass

        def iconphoto(self, default, image):
            pass

        def destroy(self):
            pass

    root = FakeRoot()
    received = {}

    monkeypatch.setattr(
        gui_application.tk,
        "Tk",
        lambda: root,
    )
    monkeypatch.setattr(
        gui_application.tk,
        "PhotoImage",
        lambda **kwargs: object(),
    )

    def fake_show_recovery_key(recovery_key, *, master):
        received["recovery_key"] = recovery_key
        received["master"] = master
        return True

    monkeypatch.setattr(
        gui_application,
        "show_recovery_key",
        fake_show_recovery_key,
    )

    def fake_unlock_application_dek(
        *,
        paths,
        prompt,
        invalid_credentials=None,
        show_recovery=None,
        on_forgot_password=None,
    ):
        received["paths"] = paths
        received["show_recovery"] = show_recovery

        if show_recovery is not None:
            received["confirmed"] = show_recovery(
                "test-recovery-key"
            )

        return None

    monkeypatch.setattr(
        gui_application,
        "unlock_application_dek",
        fake_unlock_application_dek,
    )

    monkeypatch.setattr(
        gui_application,
        "build_view_model",
        lambda **kwargs: pytest.fail(
            "build_view_model must not run"
        ),
    )

    result = gui_application.run_gui(
        ["garlicsmtp-gui"],
        paths=paths,
    )

    assert result == 1
    assert received["paths"] == paths
    assert callable(received["show_recovery"])
    assert received["recovery_key"] == "test-recovery-key"
    assert received["master"] is root
    assert received["confirmed"] is True


def test_gui_resume_recovery_dialog_error_preserves_dek(tmp_path):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )

    store = AccountCredentialStore(
        path=paths.account_credentials_file,
    )
    store.create(
        username="alice",
        password="Garlic1!",
    )
    store.enable_recovery(
        username="alice",
        password="Garlic1!",
        recovery_key="old-recovery-key",
    )

    original_dek = store.unlock_dek_with_password(
        username="alice",
        password="Garlic1!",
    )

    displayed_keys = []

    def failing_show_recovery(recovery_key):
        displayed_keys.append(recovery_key)
        raise RuntimeError("Recovery dialog failed")

    with pytest.raises(RuntimeError, match="Recovery dialog failed"):
        gui_application.unlock_application_dek(
            paths=paths,
            prompt=lambda: ("alice", "Garlic1!"),
            show_recovery=failing_show_recovery,
        )

    assert len(displayed_keys) == 1
    assert store._read_credentials()["recovery_confirmed"] is False

    assert store.unlock_dek_with_password(
        username="alice",
        password="Garlic1!",
    ) == original_dek

    assert store.unlock_dek_with_recovery(
        username="alice",
        recovery_key=displayed_keys[0],
    ) == original_dek


def test_gui_resume_recovery_confirmation_failure_preserves_dek(
    tmp_path,
    monkeypatch,
):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )

    store = AccountCredentialStore(
        path=paths.account_credentials_file,
    )
    store.create(
        username="alice",
        password="Garlic1!",
    )
    store.enable_recovery(
        username="alice",
        password="Garlic1!",
        recovery_key="old-recovery-key",
    )

    original_dek = store.unlock_dek_with_password(
        username="alice",
        password="Garlic1!",
    )

    displayed_keys = []

    def show_recovery(recovery_key):
        displayed_keys.append(recovery_key)
        return recovery_key

    original_replace = AccountCredentialStore._replace_credentials

    def fail_confirmation(self, data, *, expected_original):
        if data.get("recovery_confirmed") is True:
            raise OSError("Simulated confirmation write failure")

        return original_replace(
            self,
            data,
            expected_original=expected_original,
        )

    monkeypatch.setattr(
        AccountCredentialStore,
        "_replace_credentials",
        fail_confirmation,
    )

    with pytest.raises(
        OSError,
        match="Simulated confirmation write failure",
    ):
        gui_application.unlock_application_dek(
            paths=paths,
            prompt=lambda: ("alice", "Garlic1!"),
            show_recovery=show_recovery,
        )

    assert len(displayed_keys) == 1

    credentials = store._read_credentials()
    assert credentials["recovery_confirmed"] is False

    assert store.unlock_dek_with_password(
        username="alice",
        password="Garlic1!",
    ) == original_dek

    assert store.unlock_dek_with_recovery(
        username="alice",
        recovery_key=displayed_keys[0],
    ) == original_dek


def test_gui_resume_recovery_directory_fsync_failure_blocks_unlock(
    tmp_path,
    monkeypatch,
):
    import os
    import stat

    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )

    store = AccountCredentialStore(
        path=paths.account_credentials_file,
    )
    store.create(
        username="alice",
        password="Garlic1!",
    )
    store.enable_recovery(
        username="alice",
        password="Garlic1!",
        recovery_key="old-recovery-key",
    )

    original_dek = store.unlock_dek_with_password(
        username="alice",
        password="Garlic1!",
    )

    displayed_keys = []
    original_confirm = AccountCredentialStore.confirm_recovery

    def fail_after_confirmation(self, *, username, recovery_key):
        import garlicsmtp.security.auth.account_credentials as credentials_module

        original_fsync = credentials_module.os.fsync

        def fail_directory_fsync(descriptor):
            if stat.S_ISDIR(os.fstat(descriptor).st_mode):
                raise OSError("Simulated directory fsync failure")
            return original_fsync(descriptor)

        with monkeypatch.context() as patch:
            patch.setattr(
                credentials_module.os,
                "fsync",
                fail_directory_fsync,
            )
            return original_confirm(self, username=username, recovery_key=recovery_key)

    monkeypatch.setattr(
        AccountCredentialStore,
        "confirm_recovery",
        fail_after_confirmation,
    )

    with pytest.raises(
        OSError,
        match="Simulated directory fsync failure",
    ):
        gui_application.unlock_application_dek(
            paths=paths,
            prompt=lambda: ("alice", "Garlic1!"),
            show_recovery=lambda key: (
                displayed_keys.append(key),
                key,
            )[1],
        )

    assert len(displayed_keys) == 1

    assert store._read_credentials()["recovery_confirmed"] is True

    assert store.unlock_dek_with_password(
        username="alice",
        password="Garlic1!",
    ) == original_dek

    assert store.unlock_dek_with_recovery(
        username="alice",
        recovery_key=displayed_keys[0],
    ) == original_dek


def test_run_gui_destroys_root_when_dek_unlock_raises(
    tmp_path,
    monkeypatch,
):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )

    paths.account_credentials_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    paths.account_credentials_file.touch()

    class FakeRoot:
        def __init__(self):
            self.destroy_calls = 0

        def title(self, value):
            pass

        def geometry(self, value):
            pass

        def withdraw(self):
            pass

        def iconphoto(self, default, image):
            pass

        def destroy(self):
            self.destroy_calls += 1

    root = FakeRoot()

    monkeypatch.setattr(
        gui_application.tk,
        "Tk",
        lambda: root,
    )

    monkeypatch.setattr(
        gui_application.tk,
        "PhotoImage",
        lambda **kwargs: object(),
    )

    monkeypatch.setattr(
        gui_application,
        "configure_application_fonts",
        lambda root: None,
    )

    def fail_unlock(**kwargs):
        raise OSError("Simulated DEK unlock failure")

    monkeypatch.setattr(
        gui_application,
        "unlock_application_dek",
        fail_unlock,
    )

    monkeypatch.setattr(
        gui_application,
        "build_view_model",
        lambda **kwargs: pytest.fail(
            "build_view_model must not run"
        ),
    )

    with pytest.raises(
        OSError,
        match="Simulated DEK unlock failure",
    ):
        gui_application.run_gui(
            ["garlicsmtp-gui"],
            paths=paths,
        )

    assert root.destroy_calls == 1


def test_run_gui_destroys_root_when_first_setup_raises_oserror(
    tmp_path,
    monkeypatch,
):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )

    events = []

    class FakeRoot:
        def title(self, value):
            pass

        def geometry(self, value):
            pass

        def withdraw(self):
            events.append("withdraw")

        def iconphoto(self, default, image):
            pass

        def destroy(self):
            events.append("destroy")

    root = FakeRoot()

    monkeypatch.setattr(
        gui_application.tk,
        "Tk",
        lambda: root,
    )

    monkeypatch.setattr(
        gui_application.tk,
        "PhotoImage",
        lambda **kwargs: object(),
    )

    monkeypatch.setattr(
        gui_application,
        "configure_application_fonts",
        lambda root: None,
    )

    monkeypatch.setattr(
        gui_application,
        "prompt_setup",
        lambda master: ("alice", "Garlic1!", "Garlic1!"),
    )

    def fail_setup(**kwargs):
        raise OSError("Simulated setup persistence failure")

    monkeypatch.setattr(
        gui_application,
        "setup_application_dek",
        fail_setup,
    )

    monkeypatch.setattr(
        gui_application,
        "build_view_model",
        lambda **kwargs: pytest.fail(
            "build_view_model must not run"
        ),
    )

    with pytest.raises(
        OSError,
        match="Simulated setup persistence failure",
    ):
        gui_application.run_gui(
            ["garlicsmtp-gui"],
            paths=paths,
        )

    assert events == ["withdraw", "destroy"]


def test_run_gui_destroys_root_when_first_setup_raises_runtime_error(
    tmp_path,
    monkeypatch,
):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )

    events = []

    class FakeRoot:
        def title(self, value):
            pass

        def geometry(self, value):
            pass

        def withdraw(self):
            events.append("withdraw")

        def iconphoto(self, default, image):
            pass

        def destroy(self):
            events.append("destroy")

    root = FakeRoot()

    monkeypatch.setattr(
        gui_application.tk,
        "Tk",
        lambda: root,
    )

    monkeypatch.setattr(
        gui_application.tk,
        "PhotoImage",
        lambda **kwargs: object(),
    )

    monkeypatch.setattr(
        gui_application,
        "configure_application_fonts",
        lambda root: None,
    )

    monkeypatch.setattr(
        gui_application,
        "prompt_setup",
        lambda master: ("alice", "Garlic1!", "Garlic1!"),
    )

    def fail_setup(**kwargs):
        raise RuntimeError("Simulated recovery dialog failure")

    monkeypatch.setattr(
        gui_application,
        "setup_application_dek",
        fail_setup,
    )

    monkeypatch.setattr(
        gui_application,
        "build_view_model",
        lambda **kwargs: pytest.fail(
            "build_view_model must not run"
        ),
    )

    with pytest.raises(
        RuntimeError,
        match="Simulated recovery dialog failure",
    ):
        gui_application.run_gui(
            ["garlicsmtp-gui"],
            paths=paths,
        )

    assert events == ["withdraw", "destroy"]


def test_run_gui_destroys_root_when_view_model_build_fails(
    tmp_path,
    monkeypatch,
):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )

    events = []
    dek = bytes(range(32))

    class FakeRoot:
        def title(self, value):
            pass

        def geometry(self, value):
            pass

        def withdraw(self):
            events.append("withdraw")

        def deiconify(self):
            events.append("deiconify")

        def iconphoto(self, default, image):
            pass

        def destroy(self):
            events.append("destroy")

    root = FakeRoot()

    monkeypatch.setattr(
        gui_application.tk,
        "Tk",
        lambda: root,
    )

    monkeypatch.setattr(
        gui_application.tk,
        "PhotoImage",
        lambda **kwargs: object(),
    )

    monkeypatch.setattr(
        gui_application,
        "configure_application_fonts",
        lambda root: None,
    )

    def fail_build(*, paths, dek):
        events.append("build")
        raise RuntimeError("Simulated view model failure")

    monkeypatch.setattr(
        gui_application,
        "build_view_model",
        fail_build,
    )

    monkeypatch.setattr(
        gui_application,
        "MainWindow",
        lambda *args, **kwargs: pytest.fail(
            "MainWindow must not be created"
        ),
    )

    with pytest.raises(
        RuntimeError,
        match="Simulated view model failure",
    ):
        gui_application.run_gui(
            ["garlicsmtp-gui"],
            paths=paths,
            authenticate=lambda **kwargs: dek,
        )

    assert events == [
        "withdraw",
        "build",
        "destroy",
    ]


def test_sent_database_wrong_dek_preserves_existing_message(
    tmp_path,
    dek,
):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )

    paths.sent_mailbox_database.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    sender = "alice@test.onion"
    body = "SENT-WRONG-DEK-PRESERVATION"

    message = MailMessage(
        envelope=Envelope(
            sender=sender,
            recipients=["bob@test.onion"],
        ),
        headers=MailHeaders(),
        body=body,
    )

    backend = SQLiteMessageStoreBackend(
        paths.sent_mailbox_database,
        dek=dek,
    )

    try:
        backend.save_entry(sender, message)
    finally:
        backend.close()

    original_bytes = (
        paths.sent_mailbox_database.read_bytes()
    )

    assert body.encode() not in original_bytes
    assert not original_bytes.startswith(
        b"SQLite format 3"
    )

    wrong_dek = bytes(
        value ^ 0xFF for value in dek
    )

    with pytest.raises(sqlcipher.DatabaseError):
        SQLiteMessageStoreBackend(
            paths.sent_mailbox_database,
            dek=wrong_dek,
        )

    assert (
        paths.sent_mailbox_database.read_bytes()
        == original_bytes
    )

    reopened = SQLiteMessageStoreBackend(
        paths.sent_mailbox_database,
        dek=dek,
    )

    try:
        entries = reopened.list_entries(sender)

        assert len(entries) == 1
        assert entries[0].message.body == body
    finally:
        reopened.close()


def test_fresh_install_creates_encrypted_databases_and_reopens(
    tmp_path,
    monkeypatch,
):
    import sqlite3

    from garlicsmtp.security.encrypted_sqlite import (
        connect_encrypted_sqlite,
    )

    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )

    # Il test non deve utilizzare la configurazione reale.
    real_builder = ApplicationBuilder

    def isolated_builder(*, paths, dek):
        return real_builder(
            paths=paths,
            settings=ApplicationSettings(),
            dek=dek,
        )

    monkeypatch.setattr(
        gui_application,
        "ApplicationBuilder",
        isolated_builder,
    )

    recovery_keys = []

    dek = gui_application.setup_application_dek(
        paths=paths,
        username="alice",
        password="Garlic1!",
        show_recovery=lambda key: (
            recovery_keys.append(key),
            key,
        )[1],
    )

    assert len(recovery_keys) == 1

    first_view_model = gui_application.build_view_model(
        paths=paths,
        dek=dek,
    )

    first_context = first_view_model.controller.context

    first_context.store.backend.close()
    first_context.queue.backend.close()

    # Chiude anche il database dei messaggi inviati.
    first_view_model.sent_message_list.explorer.store.backend.close()

    reopened_store = AccountCredentialStore(
        path=paths.account_credentials_file,
    )

    reopened_dek = reopened_store.unlock_dek_with_password(
        username="alice",
        password="Garlic1!",
    )

    assert reopened_dek == dek

    recovered_dek = reopened_store.unlock_dek_with_recovery(
        username="alice",
        recovery_key=recovery_keys[0],
    )

    assert recovered_dek == dek

    attachment_content = (
        b"GarlicSMTP confidential attachment "
        b"content for fresh install test"
    )

    first_context.store.attachment_store.save(
        message_id="fresh-install-message",
        filename="private.txt",
        declared_mime="text/plain",
        content=attachment_content,
    )

    encrypted_files = list(
        (
            paths.attachments_dir
            / "fresh-install-message"
        ).glob("*.gsat")
    )

    assert len(encrypted_files) == 1

    encrypted_bytes = encrypted_files[0].read_bytes()

    assert encrypted_bytes.startswith(b"GSAT\x01")
    assert attachment_content not in encrypted_bytes
    assert b"private.txt" not in encrypted_bytes

    recovered_attachment_store = AttachmentStore(
        paths.attachments_dir,
        dek=recovered_dek,
    )

    recovered_attachments = (
        recovered_attachment_store.list_for_message(
            "fresh-install-message"
        )
    )

    assert len(recovered_attachments) == 1
    assert recovered_attachments[0].filename == "private.txt"
    assert recovered_attachments[0].declared_mime == "text/plain"
    assert recovered_attachments[0].content == attachment_content

    for database in (
        paths.mailbox_database,
        paths.sent_mailbox_database,
        paths.queue_database,
    ):
        connection = connect_encrypted_sqlite(
            database,
            dek=recovered_dek,
        )
        try:
            assert connection.execute(
                "PRAGMA integrity_check"
            ).fetchone() == ("ok",)
        finally:
            connection.close()

    for database in (
        paths.mailbox_database,
        paths.sent_mailbox_database,
        paths.queue_database,
    ):
        assert database.is_file()

        assert database.read_bytes()[:16] != (
            b"SQLite format 3\x00"
        )

        with pytest.raises(sqlite3.DatabaseError):
            with sqlite3.connect(database) as connection:
                connection.execute(
                    "SELECT name FROM sqlite_master"
                ).fetchall()

        connection = connect_encrypted_sqlite(
            database,
            dek=reopened_dek,
        )
        try:
            assert connection.execute(
                "PRAGMA integrity_check"
            ).fetchone() == ("ok",)
        finally:
            connection.close()

        second_view_model = gui_application.build_view_model(
            paths=paths,
            dek=reopened_dek,
        )

        second_context = second_view_model.controller.context

        reopened_attachments = (
            second_context.store.attachment_store.list_for_message(
                "fresh-install-message"
            )
        )

        assert len(reopened_attachments) == 1
        assert reopened_attachments[0].filename == "private.txt"
        assert reopened_attachments[0].declared_mime == "text/plain"
        assert reopened_attachments[0].content == attachment_content

        assert second_context.store is not None
        assert second_context.queue is not None

        second_context.store.backend.close()
        second_context.queue.backend.close()

        second_view_model.sent_message_list.explorer.store.backend.close()

def test_gui_setup_rejects_wrong_reentered_recovery_key(tmp_path):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )

    with pytest.raises(ValueError):
        gui_application.setup_application_dek(
            paths=paths,
            username="alice",
            password="Garlic1!",
            show_recovery=lambda recovery_key: "wrong-recovery-key",
        )

    credentials = json.loads(
        paths.account_credentials_file.read_text(
            encoding="utf-8",
        )
    )

    assert credentials["recovery_confirmed"] is False


def test_gui_setup_accepts_correct_reentered_recovery_key(tmp_path):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )

    displayed_recovery_keys = []

    def show_recovery(recovery_key):
        displayed_recovery_keys.append(recovery_key)
        return recovery_key

    dek = gui_application.setup_application_dek(
        paths=paths,
        username="alice",
        password="Garlic1!",
        show_recovery=show_recovery,
    )

    assert len(displayed_recovery_keys) == 1
    assert isinstance(dek, bytes)
    assert len(dek) == 32

    store = AccountCredentialStore(
        path=paths.account_credentials_file,
    )

    assert store._read_credentials()["recovery_confirmed"] is True

    assert store.unlock_dek_with_recovery(
        username="alice",
        recovery_key=displayed_recovery_keys[0],
    ) == dek


def test_gui_unlock_accepts_correct_reentered_recovery_key(tmp_path):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )

    store = AccountCredentialStore(
        path=paths.account_credentials_file,
    )
    store.create(
        username="alice",
        password="Garlic1!",
    )
    store.enable_recovery(
        username="alice",
        password="Garlic1!",
        recovery_key="old-unconfirmed-recovery-key",
    )

    expected_dek = store.unlock_dek_with_password(
        username="alice",
        password="Garlic1!",
    )

    displayed_keys = []

    def show_recovery(recovery_key):
        displayed_keys.append(recovery_key)
        return recovery_key

    actual_dek = gui_application.unlock_application_dek(
        paths=paths,
        prompt=lambda: ("alice", "Garlic1!"),
        show_recovery=show_recovery,
    )

    assert actual_dek == expected_dek
    assert len(displayed_keys) == 1

    assert store._read_credentials()["recovery_confirmed"] is True

    assert store.unlock_dek_with_recovery(
        username="alice",
        recovery_key=displayed_keys[0],
    ) == expected_dek


def test_gui_unlock_rejects_wrong_reentered_recovery_key(tmp_path):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp",
    )

    store = AccountCredentialStore(
        path=paths.account_credentials_file,
    )
    store.create(
        username="alice",
        password="Garlic1!",
    )
    store.enable_recovery(
        username="alice",
        password="Garlic1!",
        recovery_key="old-unconfirmed-recovery-key",
    )

    expected_dek = store.unlock_dek_with_password(
        username="alice",
        password="Garlic1!",
    )

    with pytest.raises(ValueError, match="Invalid wrapped DEK"):
        gui_application.unlock_application_dek(
            paths=paths,
            prompt=lambda: ("alice", "Garlic1!"),
            show_recovery=lambda recovery_key: "wrong-recovery-key",
        )

    assert store._read_credentials()["recovery_confirmed"] is False

    assert store.unlock_dek_with_password(
        username="alice",
        password="Garlic1!",
    ) == expected_dek


def test_gui_unlock_handles_forgot_password_request(
    tmp_path,
    monkeypatch,
):
    from types import SimpleNamespace

    from garlicsmtp.gui.application import unlock_application_dek

    class FakeStore:
        def __init__(self, path):
            self.path = path

        def authenticate(self, *, username, password):
            raise AssertionError(
                "Authentication must not run for a recovery request"
            )

    monkeypatch.setattr(
        "garlicsmtp.gui.application.AccountCredentialStore",
        FakeStore,
    )

    responses = iter(["forgot_password", None])
    recovery_requests = []

    result = unlock_application_dek(
        paths=SimpleNamespace(
            account_credentials_file=tmp_path / "credentials.json",
        ),
        prompt=lambda: next(responses),
        on_forgot_password=lambda: recovery_requests.append(True),
    )

    assert result is None
    assert recovery_requests == [True]


def test_password_recovery_does_not_reset_without_key_confirmation(
    tmp_path,
    monkeypatch,
):
    from types import SimpleNamespace

    from garlicsmtp.gui.application import recover_application_password

    reset_calls = []

    class FakeStore:
        def __init__(self, path):
            self.path = path

        def reset_password_with_recovery(self, **kwargs):
            reset_calls.append(kwargs)

    monkeypatch.setattr(
        "garlicsmtp.gui.application.AccountCredentialStore",
        FakeStore,
    )

    result = recover_application_password(
        paths=SimpleNamespace(
            account_credentials_file=tmp_path / "credentials.json",
        ),
        username="test-user",
        recovery_key="existing-recovery-key",
        new_password="NewPassword123!",
        show_recovery=lambda generated_key: False,
    )

    assert result is False
    assert reset_calls == []


def test_password_recovery_resets_after_key_confirmation(
    tmp_path,
    monkeypatch,
):
    from types import SimpleNamespace

    from garlicsmtp.gui.application import recover_application_password

    generated_key = "new-generated-recovery-key"
    reset_calls = []

    class FakeKeyManager:
        def generate_recovery_key(self):
            return generated_key

    class FakeStore:
        def __init__(self, path):
            assert path == tmp_path / "credentials.json"

        def reset_password_with_recovery(self, **kwargs):
            reset_calls.append(kwargs)

    monkeypatch.setattr(
        "garlicsmtp.gui.application.AtRestKeyManager",
        FakeKeyManager,
    )
    monkeypatch.setattr(
        "garlicsmtp.gui.application.AccountCredentialStore",
        FakeStore,
    )

    result = recover_application_password(
        paths=SimpleNamespace(
            account_credentials_file=tmp_path / "credentials.json",
        ),
        username="test-user",
        recovery_key="old-recovery-key",
        new_password="NewPassword123!",
        show_recovery=lambda key: key,
    )

    assert result is True
    assert reset_calls == [{
        "username": "test-user",
        "recovery_key": "old-recovery-key",
        "new_password": "NewPassword123!",
        "new_recovery_key": generated_key,
    }]


def test_password_recovery_rejects_mismatched_confirmation(
    tmp_path,
    monkeypatch,
):
    from types import SimpleNamespace

    from garlicsmtp.gui.application import recover_application_password

    reset_calls = []

    class FakeKeyManager:
        def generate_recovery_key(self):
            return "correct-new-key"

    class FakeStore:
        def __init__(self, path):
            pass

        def reset_password_with_recovery(self, **kwargs):
            reset_calls.append(kwargs)

    monkeypatch.setattr(
        "garlicsmtp.gui.application.AtRestKeyManager",
        FakeKeyManager,
    )
    monkeypatch.setattr(
        "garlicsmtp.gui.application.AccountCredentialStore",
        FakeStore,
    )

    result = recover_application_password(
        paths=SimpleNamespace(
            account_credentials_file=tmp_path / "credentials.json",
        ),
        username="test-user",
        recovery_key="old-key",
        new_password="NewPassword123!",
        show_recovery=lambda key: "incorrect-key",
    )

    assert result is False
    assert reset_calls == []


def test_password_recovery_propagates_credential_errors(
    tmp_path,
    monkeypatch,
):
    from types import SimpleNamespace

    import pytest

    from garlicsmtp.gui.application import recover_application_password

    class FakeKeyManager:
        def generate_recovery_key(self):
            return "new-key"

    class FakeStore:
        def __init__(self, path):
            pass

        def reset_password_with_recovery(self, **kwargs):
            raise ValueError("Invalid account credentials")

    monkeypatch.setattr(
        "garlicsmtp.gui.application.AtRestKeyManager",
        FakeKeyManager,
    )
    monkeypatch.setattr(
        "garlicsmtp.gui.application.AccountCredentialStore",
        FakeStore,
    )

    with pytest.raises(ValueError, match="Invalid account credentials"):
        recover_application_password(
            paths=SimpleNamespace(
                account_credentials_file=tmp_path / "credentials.json",
            ),
            username="test-user",
            recovery_key="wrong-old-key",
            new_password="NewPassword123!",
            show_recovery=lambda key: key,
        )


def test_run_gui_wires_forgot_password_to_recovery_flow(
    tmp_path,
    monkeypatch,
):
    paths = ApplicationPaths(root_dir=tmp_path / "garlicsmtp")
    paths.account_credentials_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    paths.account_credentials_file.touch()

    events = []

    class FakeRoot:
        def title(self, value):
            pass

        def geometry(self, value):
            pass

        def withdraw(self):
            pass

        def iconphoto(self, default, image):
            pass

        def destroy(self):
            events.append(("destroy",))

    root = FakeRoot()

    def fake_showinfo(title, message, *, parent):
        events.append(("showinfo", title, message, parent))

    monkeypatch.setattr(
        gui_application.messagebox,
        "showinfo",
        fake_showinfo,
    )

    monkeypatch.setattr(gui_application.tk, "Tk", lambda: root)
    monkeypatch.setattr(
        gui_application.tk,
        "PhotoImage",
        lambda **kwargs: object(),
    )

    def fake_prompt_password_reset(master):
        events.append(("reset_prompt", master))
        return ("alice", "existing-key", "NewPassword123!")

    monkeypatch.setattr(
        gui_application,
        "prompt_password_reset",
        fake_prompt_password_reset,
        raising=False,
    )

    def fake_recover_application_password(**kwargs):
        events.append(("recover", kwargs))
        return True

    monkeypatch.setattr(
        gui_application,
        "recover_application_password",
        fake_recover_application_password,
    )

    def fake_unlock_application_dek(
        *,
        paths,
        prompt,
        invalid_credentials=None,
        show_recovery=None,
        on_forgot_password=None,
    ):
        assert callable(on_forgot_password)
        on_forgot_password()
        return None

    monkeypatch.setattr(
        gui_application,
        "unlock_application_dek",
        fake_unlock_application_dek,
    )

    monkeypatch.setattr(
        gui_application,
        "build_view_model",
        lambda **kwargs: pytest.fail(
            "Recovery must return to login, not open the application"
        ),
    )

    result = gui_application.run_gui(
        ["garlicsmtp-gui"],
        paths=paths,
    )

    assert result == 1
    assert events[0] == ("reset_prompt", root)

    recovery = events[1]
    assert recovery[0] == "recover"
    assert recovery[1]["paths"] == paths
    assert recovery[1]["username"] == "alice"
    assert recovery[1]["recovery_key"] == "existing-key"
    assert recovery[1]["new_password"] == "NewPassword123!"
    assert callable(recovery[1]["show_recovery"])
    assert events[2][0] == "showinfo"
    assert events[2][3] is root
    assert "Sign in" in events[2][2]
    assert events[-1] == ("destroy",)


@pytest.mark.parametrize(
    ("credentials", "recovery_result", "expected_message"),
    [
        (None, None, None),
        (("alice", "old-key", "NewPassword123!"), False, None),
        (("alice", "wrong-key", "NewPassword123!"), ValueError("Invalid recovery key"), "error"),
        (("alice", "old-key", "NewPassword123!"), True, "success"),
    ],
)
def test_handle_forgot_password_outcomes(
    tmp_path,
    monkeypatch,
    credentials,
    recovery_result,
    expected_message,
):
    paths = ApplicationPaths(root_dir=tmp_path / "garlicsmtp")
    master = object()
    events = []

    monkeypatch.setattr(
        gui_application,
        "prompt_password_reset",
        lambda received_master: (
            events.append(("prompt", received_master)),
            credentials,
        )[1],
    )

    def fake_recover_application_password(**kwargs):
        events.append(("recover", kwargs))
        if isinstance(recovery_result, Exception):
            raise recovery_result
        return recovery_result

    monkeypatch.setattr(
        gui_application,
        "recover_application_password",
        fake_recover_application_password,
    )

    monkeypatch.setattr(
        gui_application.messagebox,
        "showerror",
        lambda title, message, *, parent: events.append(
            ("error", title, message, parent)
        ),
    )
    monkeypatch.setattr(
        gui_application.messagebox,
        "showinfo",
        lambda title, message, *, parent: events.append(
            ("success", title, message, parent)
        ),
    )

    gui_application.handle_forgot_password(
        paths=paths,
        master=master,
    )

    assert events[0] == ("prompt", master)

    recovery_calls = [
        event for event in events if event[0] == "recover"
    ]
    messages = [
        event for event in events
        if event[0] in ("error", "success")
    ]

    if credentials is None:
        assert recovery_calls == []
    else:
        assert len(recovery_calls) == 1
        kwargs = recovery_calls[0][1]
        assert kwargs["paths"] == paths
        assert kwargs["username"] == credentials[0]
        assert kwargs["recovery_key"] == credentials[1]
        assert kwargs["new_password"] == credentials[2]
        assert callable(kwargs["show_recovery"])

    if expected_message is None:
        assert messages == []
    else:
        assert len(messages) == 1
        assert messages[0][0] == expected_message
        assert messages[0][3] is master

        if expected_message == "error":
            assert "Invalid recovery key" in messages[0][2]
        else:
            assert "Sign in" in messages[0][2]