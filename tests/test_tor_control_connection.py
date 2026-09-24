# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import socket

import pytest

from garlicsmtp.tor.control import (
    TorControlConnection,
    TorControlConnectionError,
    TorControlProtocolError,
    TorControlSecurityError,
)


class FakeSocket:

    def __init__(
        self,
        chunks=None,
    ):
        self.chunks = list(
            chunks or []
        )

        self.sent = bytearray()
        self.timeout = None
        self.closed = False

    def settimeout(
        self,
        timeout,
    ):
        self.timeout = timeout

    def sendall(
        self,
        data,
    ):
        self.sent.extend(
            data
        )

    def recv(
        self,
        size,
    ):
        if not self.chunks:
            return b""

        return self.chunks.pop(0)

    def close(
        self,
    ):
        self.closed = True


def test_tor_control_connection_connects():
    fake_socket = FakeSocket()
    calls = []

    def socket_factory(
        address,
        timeout,
    ):
        calls.append(
            (
                address,
                timeout,
            )
        )

        return fake_socket

    connection = TorControlConnection(
        host="127.0.0.1",
        port=9051,
        timeout=3.0,
        socket_factory=socket_factory,
    )

    connection.connect()

    assert connection.connected is True

    assert calls == [
        (
            (
                "127.0.0.1",
                9051,
            ),
            3.0,
        ),
    ]

    assert fake_socket.timeout == 3.0



def test_tor_control_connection_sends_crlf():
    fake_socket = FakeSocket()

    connection = TorControlConnection(
        socket_factory=(
            lambda address, timeout: (
                fake_socket
            )
        )
    )

    connection.connect()

    connection.send_line(
        "PROTOCOLINFO 1"
    )

    assert bytes(
        fake_socket.sent
    ) == b"PROTOCOLINFO 1\r\n"

def test_tor_control_connection_receives_line():
    fake_socket = FakeSocket(
        chunks=[
            b"250-PROTO",
            b"COLINFO 1\r",
            b"\n250 OK\r\n",
        ]
    )

    connection = TorControlConnection(
        socket_factory=(
            lambda address, timeout: (
                fake_socket
            )
        )
    )

    connection.connect()

    assert connection.receive_line() == (
        "250-PROTOCOLINFO 1"
    )

    assert connection.receive_line() == (
        "250 OK"
    )


@pytest.mark.parametrize(
    "host",
    [
        "0.0.0.0",
        "192.168.1.10",
        "8.8.8.8",
        "tor.example.org",
    ],
)
def test_tor_control_rejects_non_loopback_hosts(
    host,
):
    with pytest.raises(
        TorControlSecurityError
    ):
        TorControlConnection(
            host=host
        )

@pytest.mark.parametrize(
    "host",
    [
        "127.0.0.1",
        "127.0.0.2",
        "::1",
    ],
)
def test_tor_control_accepts_loopback_hosts(
    host,
):
    connection = TorControlConnection(
        host=host
    )

    assert connection.host == host


@pytest.mark.parametrize(
    "command",
    [
        "",
        "PROTOCOLINFO\r\nAUTHENTICATE",
        "PROTOCOLINFO\nAUTHENTICATE",
        "PROTOCOLINFO\rAUTHENTICATE",
    ],
)
def test_tor_control_rejects_invalid_commands(
    command,
):
    fake_socket = FakeSocket()

    connection = TorControlConnection(
        socket_factory=(
            lambda address, timeout: (
                fake_socket
            )
        )
    )

    connection.connect()

    with pytest.raises(
        TorControlProtocolError
    ):
        connection.send_line(
            command
        )

    assert fake_socket.sent == b""


def test_tor_control_connection_closes():
    fake_socket = FakeSocket()

    connection = TorControlConnection(
        socket_factory=(
            lambda address, timeout: (
                fake_socket
            )
        )
    )

    connection.connect()
    connection.close()

    assert connection.connected is False
    assert fake_socket.closed is True

    connection.close()


def test_tor_control_connection_reports_connect_error():
    def socket_factory(
        address,
        timeout,
    ):
        raise OSError(
            "connection refused"
        )

    connection = TorControlConnection(
        socket_factory=socket_factory
    )

    with pytest.raises(
        TorControlConnectionError
    ):
        connection.connect()

    assert connection.connected is False


def test_tor_control_connection_rejects_eof():
    fake_socket = FakeSocket(
        chunks=[]
    )

    connection = TorControlConnection(
        socket_factory=(
            lambda address, timeout: (
                fake_socket
            )
        )
    )

    connection.connect()

    with pytest.raises(
        TorControlConnectionError
    ):
        connection.receive_line()

    assert connection.connected is False


def test_tor_control_connection_limits_line_length():
    fake_socket = FakeSocket(
        chunks=[
            b"123456789",
        ]
    )

    connection = TorControlConnection(
        max_line_bytes=4,
        socket_factory=(
            lambda address, timeout: (
                fake_socket
            )
        ),
    )

    connection.connect()

    with pytest.raises(
        TorControlProtocolError
    ):
        connection.receive_line()

    assert connection.connected is False
