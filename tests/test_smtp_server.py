# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

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