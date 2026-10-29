# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import pytest

from garlicsmtp.network.server import TCPServer


def test_tcp_server_start_stop():
    server = TCPServer(host="127.0.0.1", port=0)

    server.start()

    assert server.socket is not None

    sock = server.socket

    server.stop()

    assert server.socket is None
    assert sock.fileno() == -1


def test_tcp_server_accept_once_without_connection():

    server = TCPServer(host="127.0.0.1", port=0)

    server.start()

    try:
        assert server.accept_once() is None
    finally:
        server.stop()


def test_tcp_server_closes_socket_when_bind_fails(monkeypatch):
    class FakeSocket:
        def __init__(self):
            self.closed = False

        def setsockopt(self, *args):
            pass

        def bind(self, address):
            raise OSError("Address already in use")

        def listen(self, backlog):
            raise AssertionError(
                "listen() must not be called after bind failure"
            )

        def close(self):
            self.closed = True

    fake_socket = FakeSocket()

    monkeypatch.setattr(
        "garlicsmtp.network.server.tcp.socket.socket",
        lambda *args, **kwargs: fake_socket,
    )

    server = TCPServer(host="127.0.0.1", port=2531)

    with pytest.raises(
        OSError,
        match="Address already in use",
    ):
        server.start()

    assert fake_socket.closed is True
    assert server.socket is None


def test_tcp_server_rejects_start_when_already_running():
    server = TCPServer(host="127.0.0.1", port=0)

    server.start()
    original_socket = server.socket

    try:
        with pytest.raises(
            RuntimeError,
            match="already started",
        ):
            server.start()

        assert server.socket is original_socket
        assert original_socket.fileno() != -1

    finally:
        server.stop()