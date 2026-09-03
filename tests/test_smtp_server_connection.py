# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.smtp.server import SMTPServer
from garlicsmtp.core.pipeline import Pipeline
from garlicsmtp.smtp.connection import SMTPConnection
from garlicsmtp.smtp.protocol import SMTPProtocol


class FakeSocket:
    def __init__(self):
        self.sent = b""
        self.buffer = [
            b"QUIT\r\n"
        ]

    def sendall(self, data: bytes):
        self.sent += data

    def recv(self, size):
        if self.buffer:
            return self.buffer.pop(0)
        return b""

    def close(self):
        pass
        

def test_smtp_server_handles_connection():
    server = SMTPServer(
        hostname="garlicsmtp.onion",
        pipeline=Pipeline(),
    )
    client = FakeSocket()

    server.handle_connection(
        client,
        ("127.0.0.1", 10000),
    )

    assert client.sent == (
        b"220 garlicsmtp.onion ready\r\n"
        b"221 Bye\r\n"
    )


def test_smtp_protocol_configures_e2ee_capability():
    class E2EEFakeSocket:

        def __init__(self):
            self.sent = b""
            self.buffer = [
                b"EHLO client\r\n",
                b"QUIT\r\n",
            ]

        def sendall(self, data: bytes):
            self.sent += data

        def recv(self, size):
            if self.buffer:
                return self.buffer.pop(0)

            return b""

        def close(self):
            pass

    client = E2EEFakeSocket()

    connection = SMTPConnection(
        client,
        ("127.0.0.1", 10000),
    )

    protocol = SMTPProtocol(
        connection,
        hostname="garlicsmtp.onion",
        pipeline=Pipeline(),
        e2ee_capability=(
            "v=1; "
            "alg=x25519; "
            "key=dGVzdA=="
        ),
    )

    protocol.serve()

    assert (
        b"GARLICSMTP-E2EE "
        b"v=1; alg=x25519; key=dGVzdA=="
        in client.sent
    )


def test_smtp_server_configures_e2ee_capability():
    class E2EEFakeSocket:

        def __init__(self):
            self.sent = b""
            self.buffer = [
                b"EHLO client\r\n",
                b"QUIT\r\n",
            ]

        def sendall(self, data: bytes):
            self.sent += data

        def recv(self, size):
            if self.buffer:
                return self.buffer.pop(0)

            return b""

        def close(self):
            pass

    server = SMTPServer(
        hostname="garlicsmtp.onion",
        pipeline=Pipeline(),
        e2ee_capability=(
            "v=1; "
            "alg=x25519; "
            "key=dGVzdA=="
        ),
    )

    client = E2EEFakeSocket()

    server.handle_connection(
        client,
        ("127.0.0.1", 10000),
    )

    assert (
        b"GARLICSMTP-E2EE "
        b"v=1; alg=x25519; key=dGVzdA=="
        in client.sent
    )