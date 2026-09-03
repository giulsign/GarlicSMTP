# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.transport.smtp.connection import SMTPConnection
from garlicsmtp.transport.smtp.protocol import SMTPClientProtocol

class FakeSocketMultiReply:

    def __init__(self):
        self.sent = b""
        self.replies = [
            b"354 End data\r\n",
            b"250 Message accepted\r\n",
        ]

    def sendall(self, data):
        self.sent += data

    def recv(self, size):
        return self.replies.pop(0)

    def close(self):
        pass

class FakeSocketQuit:

    def __init__(self):
        self.sent = b""

    def sendall(self, data):
        self.sent += data

    def recv(self, size):
        return b"221 Bye\r\n"

    def close(self):
        pass

class FakeSocket:

    def __init__(self):

        self.sent = b""

    def sendall(self, data):

        self.sent += data

    def recv(self, size):

        return b"250 OK\r\n"

    def close(self):

        pass


def test_protocol_send():

    connection = SMTPConnection()
    
    connection.socket = FakeSocket()

    connection._buffer = b""

    protocol = SMTPClientProtocol(connection)

    protocol.send_command("EHLO garlic")

    assert connection.socket.sent == b"EHLO garlic\r\n"


def test_protocol_receive():

    connection = SMTPConnection()
    
    connection.socket = FakeSocket()

    connection._buffer = b""

    protocol = SMTPClientProtocol(connection)

    reply = protocol.read_reply()

    assert reply.code == 250
    assert reply.message == "OK"

def test_protocol_ehlo():

    connection = SMTPConnection()
    
    connection.socket = FakeSocket()

    connection._buffer = b""

    protocol = SMTPClientProtocol(connection)

    reply = protocol.ehlo("garlic.onion")

    assert connection.socket.sent == (
        b"EHLO garlic.onion\r\n"
    )

    assert reply.code == 250

class FakeSocketE2EECapability:

    def __init__(self):
        self.sent = b""
        self.replies = [
            b"250-Hello garlic.onion\r\n",
            b"250-GARLICSMTP-E2EE v=1; alg=x25519; key=dGVzdA==\r\n",
            b"250 OK\r\n",
        ]

    def sendall(self, data):
        self.sent += data

    def recv(self, size):
        return self.replies.pop(0)

    def close(self):
        pass


def test_protocol_ehlo_reads_e2ee_capability():
    connection = SMTPConnection()

    connection.socket = FakeSocketE2EECapability()
    connection._buffer = b""

    protocol = SMTPClientProtocol(
        connection
    )

    reply = protocol.ehlo(
        "garlic.onion"
    )

    assert reply.code == 250
    assert reply.message == (
        "Hello garlic.onion\n"
        "GARLICSMTP-E2EE "
        "v=1; alg=x25519; key=dGVzdA==\n"
        "OK"
    )

def test_protocol_ehlo_exposes_e2ee_capability():
    connection = SMTPConnection()

    connection.socket = FakeSocketE2EECapability()
    connection._buffer = b""

    protocol = SMTPClientProtocol(
        connection
    )

    reply = protocol.ehlo(
        "garlic.onion"
    )

    assert reply.capability(
        "GARLICSMTP-E2EE"
    ) == (
        "v=1; alg=x25519; key=dGVzdA=="
    )

def test_protocol_ehlo_returns_none_for_missing_capability():
    connection = SMTPConnection()

    connection.socket = FakeSocket()
    connection._buffer = b""

    protocol = SMTPClientProtocol(
        connection
    )

    reply = protocol.ehlo(
        "garlic.onion"
    )

    assert reply.capability(
        "GARLICSMTP-E2EE"
    ) is None

def test_protocol_mail_from():

    connection = SMTPConnection()
    
    connection.socket = FakeSocket()

    connection._buffer = b""

    protocol = SMTPClientProtocol(connection)

    reply = protocol.mail_from("alice@example.com")

    assert connection.socket.sent == (
        b"MAIL FROM:<alice@example.com>\r\n"
    )

    assert reply.code == 250


def test_protocol_rcpt_to():

    connection = SMTPConnection()
    
    connection.socket = FakeSocket()

    connection._buffer = b""

    protocol = SMTPClientProtocol(connection)

    reply = protocol.rcpt_to("bob@example.com")

    assert connection.socket.sent == (
        b"RCPT TO:<bob@example.com>\r\n"
    )

    assert reply.code == 250


def test_protocol_data():

    connection = SMTPConnection()
    
    connection.socket = FakeSocketMultiReply()

    connection._buffer = b""

    protocol = SMTPClientProtocol(connection)

    reply = protocol.data("Subject: Test\r\n\r\nHello")

    assert connection.socket.sent == (
        b"DATA\r\n"
        b"Subject: Test\r\n\r\nHello\r\n.\r\n"
    )

    assert reply.code == 250


def test_protocol_quit():

    connection = SMTPConnection()
    
    connection.socket = FakeSocketQuit()

    connection._buffer = b""

    protocol = SMTPClientProtocol(connection)

    reply = protocol.quit()

    assert connection.socket.sent == b"QUIT\r\n"
    assert reply.code == 221


def test_protocol_data_dot_stuffs_leading_dots():
    connection = SMTPConnection()

    connection.socket = FakeSocketMultiReply()
    connection._buffer = b""

    protocol = SMTPClientProtocol(
        connection
    )

    reply = protocol.data(
        "line one\r\n"
        ".leading dot\r\n"
        "..two leading dots"
    )

    assert connection.socket.sent == (
        b"DATA\r\n"
        b"line one\r\n"
        b"..leading dot\r\n"
        b"...two leading dots\r\n"
        b".\r\n"
    )

    assert reply.code == 250