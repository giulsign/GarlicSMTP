# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import pytest
import threading

from garlicsmtp.core.pipeline import Pipeline
from garlicsmtp.smtp.server import SMTPServer


def build_pipeline() -> Pipeline:
    return Pipeline()


def test_smtp_server_start_stop():
    server = SMTPServer(
        host="127.0.0.1",
        port=0,
        pipeline=build_pipeline(),
    )

    server.start()

    assert server.running is True
    assert server.server.socket is not None

    server.stop()

    assert server.running is False
    assert server.server.socket is None


def test_smtp_server_tick_without_connection():
    server = SMTPServer(
        host="127.0.0.1",
        port=0,
        pipeline=build_pipeline(),
    )

    server.start()

    try:
        server.tick()
        assert server.running is True
    finally:
        server.stop()


class SpyLogger:

    def __init__(self):
        self.messages = []

    def info(self, message):
        self.messages.append(
            message
        )

    def warning(self, message):
        self.messages.append(
            message
        )

    def error(self, message):
        self.messages.append(
            message
        )


def test_smtp_server_uses_logger():
    logger = SpyLogger()

    server = SMTPServer(
        host="127.0.0.1",
        port=2530,
        logger=logger,
        pipeline=build_pipeline(),
    )

    server.start()

    try:
        assert (
            "SMTP Server listening on "
            "127.0.0.1:2530"
            in logger.messages
        )
    finally:
        server.stop()


def test_smtp_server_handles_connection_in_thread():
    entered = threading.Event()
    release = threading.Event()

    class FakeClient:

        def __init__(self):
            self.closed = False

        def close(self):
            self.closed = True

    class FakeTCPServer:

        def __init__(self):
            self.client = FakeClient()
            self.accepted = False

        def accept_once(self):
            if self.accepted:
                return None

            self.accepted = True

            return (
                self.client,
                ("127.0.0.1", 10000),
            )

        def stop(self):
            pass

    server = SMTPServer(
        host="127.0.0.1",
        port=2531,
        pipeline=build_pipeline(),
    )

    server.server = FakeTCPServer()
    server.running = True

    def fake_handle_connection(
        client,
        address,
    ):
        entered.set()
        release.wait(
            timeout=2
        )

    server.handle_connection = (
        fake_handle_connection
    )

    server.tick()

    assert entered.wait(
        timeout=1
    )

    assert (
        server.active_connections
        == 1
    )

    assert server.running is True

    release.set()

    for _ in range(100):
        if (
            server.active_connections
            == 0
        ):
            break

        threading.Event().wait(
            0.01
        )

    assert (
        server.active_connections
        == 0
    )

    assert (
        server.server.client.closed
        is True
    )


def test_smtp_server_connection_error_log_is_privacy_safe():
    logger = SpyLogger()

    server = SMTPServer(
        host="127.0.0.1",
        port=2532,
        logger=logger,
        pipeline=build_pipeline(),
    )

    class FakeClient:

        def __init__(self):
            self.closed = False

        def close(self):
            self.closed = True

    client = FakeClient()

    def fail_handle_connection(
        client,
        address,
    ):
        raise RuntimeError(
            "secret recipient "
            "bob@private.onion "
            "subject=Top Secret"
        )

    server.handle_connection = (
        fail_handle_connection
    )

    server._serve_connection(
        client,
        (
            "203.0.113.55",
            45123,
        ),
    )

    output = "\n".join(
        logger.messages
    )

    assert (
        "SMTP connection error "
        "[RuntimeError]"
        in output
    )

    assert (
        "203.0.113.55"
        not in output
    )

    assert (
        "45123"
        not in output
    )

    assert (
        "bob@private.onion"
        not in output
    )

    assert (
        "Top Secret"
        not in output
    )

    assert client.closed is True


def test_smtp_server_thread_name_does_not_expose_remote_address(
    monkeypatch,
):
    captured = {}

    class FakeClient:

        def close(self):
            pass

    class FakeTCPServer:

        def accept_once(self):
            return (
                FakeClient(),
                (
                    "203.0.113.77",
                    45678,
                ),
            )

    class FakeThread:

        def __init__(
            self,
            *,
            target,
            args,
            daemon,
            name,
        ):
            captured["name"] = name
            captured["target"] = target
            captured["args"] = args
            self._alive = False

        def start(self):
            pass

    monkeypatch.setattr(
        "garlicsmtp.smtp.server.threading.Thread",
        FakeThread,
    )

    server = SMTPServer(
        host="127.0.0.1",
        port=2533,
        pipeline=build_pipeline(),
    )

    server.server = FakeTCPServer()
    server.running = True

    server.tick()

    thread_name = captured[
        "name"
    ]

    assert (
        thread_name
        == "smtp-connection"
    )

    assert (
        "203.0.113.77"
        not in thread_name
    )

    assert (
        "45678"
        not in thread_name
    )


def test_smtp_server_passes_verifier_to_protocol(
    monkeypatch,
):
    verifier = object()
    decryptor = object()
    encryption_private_key = object()
    captured = {}

    class FakeClient:

        def close(self):
            pass

    class FakeProtocol:

        def __init__(
            self,
            connection,
            *,
            hostname,
            pipeline,
            verifier,
            e2ee_capability,
            decryptor,
            encryption_private_key,
        ):
            captured["connection"] = connection
            captured["hostname"] = hostname
            captured["pipeline"] = pipeline
            captured["verifier"] = verifier
            captured["e2ee_capability"] = (
                e2ee_capability
            )
            captured["decryptor"] = decryptor
            captured["encryption_private_key"] = (
                encryption_private_key
            )

        def serve(self):
            captured["served"] = True

    monkeypatch.setattr(
        "garlicsmtp.smtp.server.SMTPProtocol",
        FakeProtocol,
    )

    pipeline = build_pipeline()

    server = SMTPServer(
        host="127.0.0.1",
        port=0,
        hostname="test.onion",
        pipeline=pipeline,
        verifier=verifier,
        decryptor=decryptor,
        encryption_private_key=(
            encryption_private_key
        ),
    )

    client = FakeClient()

    server.handle_connection(
        client,
        ("127.0.0.1", 12345),
    )

    assert captured["hostname"] == "test.onion"
    assert captured["pipeline"] is pipeline
    assert captured["verifier"] is verifier
    assert (
        captured["e2ee_capability"]
        is None
    )
    assert captured["served"] is True
    assert captured["decryptor"] is decryptor
    assert (
        captured["encryption_private_key"]
        is encryption_private_key
    )


def test_smtp_tick_cleans_up_when_thread_start_fails(
    monkeypatch,
):
    class FakeClient:
        def __init__(self):
            self.closed = False

        def close(self):
            self.closed = True

    class FakeTCPServer:
        def __init__(self, client):
            self.client = client

        def accept_once(self):
            return (
                self.client,
                ("127.0.0.1", 10000),
            )

    client = FakeClient()

    server = SMTPServer(
        host="127.0.0.1",
        port=0,
        pipeline=build_pipeline(),
    )

    server.server = FakeTCPServer(client)
    server.running = True

    def fail_thread_start(self):
        raise RuntimeError("thread start failed")

    monkeypatch.setattr(
        "garlicsmtp.smtp.server.threading.Thread.start",
        fail_thread_start,
    )

    with pytest.raises(
        RuntimeError,
        match="thread start failed",
    ):
        server.tick()

    assert client.closed is True
    assert server.active_connections == 0


def test_smtp_stop_closes_active_client_connections():
    entered = threading.Event()
    released = threading.Event()

    class FakeClient:
        def __init__(self):
            self.closed = False

        def close(self):
            self.closed = True
            released.set()

    class FakeTCPServer:
        def __init__(self, client):
            self.client = client
            self.accepted = False

        def accept_once(self):
            if self.accepted:
                return None

            self.accepted = True
            return (
                self.client,
                ("127.0.0.1", 10000),
            )

        def stop(self):
            pass

    client = FakeClient()

    server = SMTPServer(
        host="127.0.0.1",
        port=0,
        pipeline=build_pipeline(),
    )

    server.server = FakeTCPServer(client)
    server.running = True

    def fake_handle_connection(client_socket, address):
        entered.set()
        released.wait(timeout=5)

    server.handle_connection = fake_handle_connection

    server.tick()

    assert entered.wait(timeout=1)
    assert server.active_connections == 1

    server.stop()

    assert client.closed is True
    assert server.active_connections == 0


def test_smtp_tick_does_not_start_connection_after_stop():
    accept_entered = threading.Event()
    release_accept = threading.Event()

    class FakeClient:
        def __init__(self):
            self.closed = False

        def close(self):
            self.closed = True

    class FakeTCPServer:
        def __init__(self, client):
            self.client = client

        def accept_once(self):
            accept_entered.set()

            assert release_accept.wait(
                timeout=5
            )

            return (
                self.client,
                ("127.0.0.1", 10000),
            )

        def stop(self):
            pass

    client = FakeClient()

    server = SMTPServer(
        host="127.0.0.1",
        port=0,
        pipeline=build_pipeline(),
    )

    server.server = FakeTCPServer(client)
    server.running = True

    connection_started = threading.Event()

    def fake_handle_connection(
        client_socket,
        address,
    ):
        connection_started.set()

    server.handle_connection = (
        fake_handle_connection
    )

    tick_thread = threading.Thread(
        target=server.tick,
    )

    tick_thread.start()

    try:
        assert accept_entered.wait(
            timeout=2
        )

        server.stop()

    finally:
        release_accept.set()
        tick_thread.join(timeout=5)

    assert not tick_thread.is_alive()
    assert client.closed is True
    assert connection_started.is_set() is False
    assert server.active_connections == 0


def test_smtp_stop_handles_registered_thread_not_yet_started(
    monkeypatch,
):
    start_entered = threading.Event()
    release_start = threading.Event()

    class FakeClient:
        def __init__(self):
            self.closed = False

        def shutdown(self, how):
            pass

        def close(self):
            self.closed = True

    class FakeTCPServer:
        def __init__(self, client):
            self.client = client
            self.accepted = False

        def accept_once(self):
            if self.accepted:
                return None

            self.accepted = True

            return (
                self.client,
                ("127.0.0.1", 10000),
            )

        def stop(self):
            pass

    client = FakeClient()

    server = SMTPServer(
        host="127.0.0.1",
        port=0,
        pipeline=build_pipeline(),
    )

    server.server = FakeTCPServer(client)
    server.running = True

    original_start = threading.Thread.start

    def delayed_start(self):
        if self.name == "smtp-connection":
            start_entered.set()

            assert release_start.wait(
                timeout=5
            )

        return original_start(self)

    monkeypatch.setattr(
        "garlicsmtp.smtp.server.threading.Thread.start",
        delayed_start,
    )

    tick_thread = threading.Thread(
        target=server.tick,
        name="smtp-tick-test",
    )

    tick_thread.start()

    stop_finished = threading.Event()
    stop_errors = []

    def stop_server():
        try:
            server.stop()
        except Exception as exc:
            stop_errors.append(exc)
        finally:
            stop_finished.set()

    stop_thread = threading.Thread(
        target=stop_server,
        name="smtp-stop-test",
    )

    try:
        assert start_entered.wait(timeout=2)

        stop_thread.start()

        # stop() deve attendere che thread.start()
        # abbia completato la fase protetta dal lock.
        assert not stop_finished.wait(timeout=0.1)

    finally:
        release_start.set()
        tick_thread.join(timeout=5)

        if stop_thread.ident is not None:
            stop_thread.join(timeout=5)

    assert not tick_thread.is_alive()
    assert not stop_thread.is_alive()
    assert stop_finished.is_set()
    assert stop_errors == []
    assert client.closed is True
    assert server.active_connections == 0