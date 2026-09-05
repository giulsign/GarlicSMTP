# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.smtp.server import SMTPServer
from garlicsmtp.core.pipeline import Pipeline
from garlicsmtp.smtp.connection import SMTPConnection
from garlicsmtp.smtp.protocol import SMTPProtocol
from garlicsmtp.storage.entry import (
    VerificationStatus,
)
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
)

from garlicsmtp.models import (
    Envelope,
    MailHeaders,
    MailMessage,
)
from garlicsmtp.security.decryptor import (
    MessageDecryptor,
)
from garlicsmtp.transport.smtp.client import (
    SMTPClient,
)
from garlicsmtp.security.encryptor import MessageEncryptor

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


def test_smtp_protocol_decrypts_before_verification():
    events = []

    class DataSocket:

        def __init__(self):
            self.sent = b""
            self.buffer = [
                b"EHLO client\r\n",
                b"MAIL FROM:<alice@sender.onion>\r\n",
                b"RCPT TO:<bob@local.onion>\r\n",
                b"DATA\r\n",
                (
                    b"X-GarlicSMTP-Encryption: "
                    b"fake\r\n"
                ),
                b"\r\n",
                b"ciphertext\r\n",
                b".\r\n",
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

    class FakeDecryptor:

        def decrypt(
            self,
            message,
            private_key,
        ):
            events.append(
                ("decrypt", message)
            )

            message.body = "plaintext"

            return message

    class FakeVerifier:

        def verify(self, message):
            events.append(
                ("verify", message)
            )

            assert message.body == "plaintext"

            return VerificationStatus.VERIFIED

    class CapturePipeline:

        def execute(self, context):
            events.append(
                ("pipeline", context.message)
            )

            assert (
                context.message.body
                == "plaintext"
            )

            assert (
                context.verification_status
                == VerificationStatus.VERIFIED
            )

            return context

    client = DataSocket()

    connection = SMTPConnection(
        client,
        ("127.0.0.1", 10000),
    )

    protocol = SMTPProtocol(
        connection,
        hostname="local.onion",
        pipeline=CapturePipeline(),
        verifier=FakeVerifier(),
        decryptor=FakeDecryptor(),
        encryption_private_key=object(),
    )

    protocol.serve()

    assert [
        event[0]
        for event in events
    ] == [
        "decrypt",
        "verify",
        "pipeline",
    ]


def test_smtp_protocol_decrypts_real_e2ee_message():
    private_key = X25519PrivateKey.generate()

    headers = MailHeaders()
    headers.add(
        "Subject",
        "INBOUND-SECRET-SUBJECT",
    )

    plaintext = MailMessage(
        envelope=Envelope(
            sender="alice@sender.onion",
            recipients=[
                "bob@local.onion",
            ],
        ),
        headers=headers,
        body="INBOUND-SECRET-BODY",
    )

    encrypted = MessageEncryptor().encrypt(
        plaintext,
        private_key.public_key(),
    )

    wire_message = SMTPClient.serialize_message(
        encrypted
    )

    captured = {}

    class DataSocket:

        def __init__(self):
            self.sent = b""

            data_lines = [
                line.encode("utf-8") + b"\r\n"
                for line in wire_message.split(
                    "\r\n"
                )
            ]

            self.buffer = [
                b"EHLO client\r\n",
                (
                    b"MAIL FROM:"
                    b"<alice@sender.onion>\r\n"
                ),
                (
                    b"RCPT TO:"
                    b"<bob@local.onion>\r\n"
                ),
                b"DATA\r\n",
                *data_lines,
                b".\r\n",
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

    class CaptureVerifier:

        def verify(self, message):
            captured["verified"] = message

            assert (
                message.headers.get("Subject")
                == "INBOUND-SECRET-SUBJECT"
            )
            assert (
                message.body
                == "INBOUND-SECRET-BODY"
            )

            return VerificationStatus.VERIFIED

    class CapturePipeline:

        def execute(self, context):
            captured["context"] = context

            return context

    client = DataSocket()

    connection = SMTPConnection(
        client,
        ("127.0.0.1", 10000),
    )

    protocol = SMTPProtocol(
        connection,
        hostname="local.onion",
        pipeline=CapturePipeline(),
        verifier=CaptureVerifier(),
        decryptor=MessageDecryptor(),
        encryption_private_key=private_key,
    )

    protocol.serve()

    message = captured["context"].message

    assert (
        message is captured["verified"]
    )
    assert (
        message.envelope.sender
        == "alice@sender.onion"
    )
    assert message.envelope.recipients == [
        "bob@local.onion",
    ]
    assert (
        message.headers.get("Subject")
        == "INBOUND-SECRET-SUBJECT"
    )
    assert (
        message.body
        == "INBOUND-SECRET-BODY"
    )
    assert (
        captured["context"]
        .verification_status
        == VerificationStatus.VERIFIED
    )


def test_smtp_protocol_rejects_e2ee_decryption_failure():
    events = []

    class FakeConnection:
        def __init__(self):
            self.ip = "127.0.0.1"

            self.lines = iter([
                "EHLO sender.onion",
                "MAIL FROM:<alice@sender.onion>",
                "RCPT TO:<bob@local.onion>",
                "DATA",
                "X-GarlicSMTP-Encryption: fake",
                "",
                "ciphertext",
                ".",
                "QUIT",
            ])
            self.sent = []

        def receive_line(self):
            return next(self.lines, None)

        def send(self, data):
            self.sent.append(data)

        def close(self):
            pass

        def peer(self):
            return ("127.0.0.1", 12345)

    class FakeDecryptor:
        def decrypt(
            self,
            message,
            private_key,
        ):
            events.append("decrypt")
            raise ValueError(
                "invalid encrypted message"
            )

    class FakeVerifier:
        def verify(self, message):
            events.append("verify")
            return VerificationStatus.VERIFIED

    class FakePipeline:
        def execute(self, context):
            events.append("pipeline")
            return context

    connection = FakeConnection()

    protocol = SMTPProtocol(
        connection,
        hostname="local.onion",
        pipeline=FakePipeline(),
        verifier=FakeVerifier(),
        decryptor=FakeDecryptor(),
        encryption_private_key=object(),
    )

    protocol.serve()

    assert events == ["decrypt"]

    assert any(
        reply.startswith(
            b"554 Transaction failed"
        )
        for reply in connection.sent
    )


def test_smtp_protocol_rejects_tampered_real_e2ee_message():
    import base64

    private_key = X25519PrivateKey.generate()

    plaintext = MailMessage(
        envelope=Envelope(
            sender="alice@sender.onion",
            recipients=[
                "bob@local.onion",
            ],
        ),
        headers=MailHeaders(
            fields={
                "Subject": "INBOUND-SECRET-SUBJECT",
            }
        ),
        body="INBOUND-SECRET-BODY",
    )

    encrypted = MessageEncryptor().encrypt(
        plaintext,
        private_key.public_key(),
    )

    ciphertext = bytearray(
        base64.b64decode(
            encrypted.body
        )
    )

    ciphertext[-1] ^= 0x01

    encrypted.body = base64.b64encode(
        bytes(ciphertext)
    ).decode("ascii")

    serialized = SMTPClient.serialize_message(
        encrypted
    )

    lines = [
        "EHLO sender.onion",
        "MAIL FROM:<alice@sender.onion>",
        "RCPT TO:<bob@local.onion>",
        "DATA",
        *serialized.splitlines(),
        ".",
        "QUIT",
    ]

    events = []

    class FakeConnection:
        def __init__(self):
            self.ip = "127.0.0.1"
            self.lines = iter(lines)
            self.sent = []

        def receive_line(self):
            return next(
                self.lines,
                None,
            )

        def send(self, data):
            self.sent.append(data)

        def close(self):
            pass

    class CaptureVerifier:
        def verify(self, message):
            events.append("verify")
            return VerificationStatus.VERIFIED

    class CapturePipeline:
        def execute(self, context):
            events.append("pipeline")
            return context

    connection = FakeConnection()

    protocol = SMTPProtocol(
        connection,
        hostname="local.onion",
        pipeline=CapturePipeline(),
        verifier=CaptureVerifier(),
        decryptor=MessageDecryptor(),
        encryption_private_key=private_key,
    )

    protocol.serve()

    assert events == []


def test_smtp_protocol_rejects_tampered_e2ee_recipient_aad():
    private_key = X25519PrivateKey.generate()

    plaintext = MailMessage(
        envelope=Envelope(
            sender="alice@sender.onion",
            recipients=[
                "bob@local.onion",
            ],
        ),
        headers=MailHeaders(
            fields={
                "Subject": "INBOUND-SECRET-SUBJECT",
            }
        ),
        body="INBOUND-SECRET-BODY",
    )

    encrypted = MessageEncryptor().encrypt(
        plaintext,
        private_key.public_key(),
    )

    serialized = SMTPClient.serialize_message(
        encrypted
    )

    lines = [
        "EHLO sender.onion",
        "MAIL FROM:<alice@sender.onion>",

        # L'envelope autenticato durante la cifratura
        # contiene bob@local.onion, ma sul wire SMTP
        # dichiariamo un destinatario diverso.
        "RCPT TO:<mallory@local.onion>",

        "DATA",
        *serialized.splitlines(),
        ".",
        "QUIT",
    ]

    events = []

    class FakeConnection:
        def __init__(self):
            self.ip = "127.0.0.1"
            self.lines = iter(lines)
            self.sent = []

        def receive_line(self):
            return next(
                self.lines,
                None,
            )

        def send(self, data):
            self.sent.append(data)

        def close(self):
            pass

    class CaptureVerifier:
        def verify(self, message):
            events.append("verify")
            return VerificationStatus.VERIFIED

    class CapturePipeline:
        def execute(self, context):
            events.append("pipeline")
            return context

    connection = FakeConnection()

    protocol = SMTPProtocol(
        connection,
        hostname="local.onion",
        pipeline=CapturePipeline(),
        verifier=CaptureVerifier(),
        decryptor=MessageDecryptor(),
        encryption_private_key=private_key,
    )

    protocol.serve()

    assert events == []

    assert any(
        reply.startswith(
            b"554 Transaction failed"
        )
        for reply in connection.sent
    )


def test_smtp_protocol_rejects_tampered_e2ee_sender_aad():
    private_key = X25519PrivateKey.generate()

    plaintext = MailMessage(
        envelope=Envelope(
            sender="alice@sender.onion",
            recipients=[
                "bob@local.onion",
            ],
        ),
        headers=MailHeaders(
            fields={
                "Subject": "INBOUND-SECRET-SUBJECT",
            }
        ),
        body="INBOUND-SECRET-BODY",
    )

    encrypted = MessageEncryptor().encrypt(
        plaintext,
        private_key.public_key(),
    )

    serialized = SMTPClient.serialize_message(
        encrypted
    )

    lines = [
        "EHLO sender.onion",
        # Il messaggio è stato cifrato con
        # alice@sender.onion nell'envelope autenticato.
        "MAIL FROM:<mallory@sender.onion>",

        # Il recipient rimane quello originale.
        "RCPT TO:<bob@local.onion>",

        "DATA",
        *serialized.splitlines(),
        ".",
        "QUIT",
    ]

    events = []

    class FakeConnection:
        def __init__(self):
            self.ip = "127.0.0.1"
            self.lines = iter(lines)
            self.sent = []

        def receive_line(self):
            return next(
                self.lines,
                None,
            )

        def send(self, data):
            self.sent.append(data)

        def close(self):
            pass

    class CaptureVerifier:
        def verify(self, message):
            events.append("verify")
            return VerificationStatus.VERIFIED

    class CapturePipeline:
        def execute(self, context):
            events.append("pipeline")
            return context

    connection = FakeConnection()

    protocol = SMTPProtocol(
        connection,
        hostname="local.onion",
        pipeline=CapturePipeline(),
        verifier=CaptureVerifier(),
        decryptor=MessageDecryptor(),
        encryption_private_key=private_key,
    )

    protocol.serve()

    assert events == []

    assert any(
        reply.startswith(
            b"554 Transaction failed"
        )
        for reply in connection.sent
    )


def test_smtp_protocol_rejects_e2ee_message_without_decryptor():
    events = []

    class FakeConnection:
        def __init__(self):
            self.ip = "127.0.0.1"

            self.lines = iter([
                "EHLO sender.onion",
                "MAIL FROM:<alice@sender.onion>",
                "RCPT TO:<bob@local.onion>",
                "DATA",
                "X-GarlicSMTP-Encryption: fake",
                "",
                "ciphertext",
                ".",
                "QUIT",
            ])

            self.sent = []

        def receive_line(self):
            return next(
                self.lines,
                None,
            )

        def send(self, data):
            self.sent.append(data)

        def close(self):
            pass

    class FakeVerifier:
        def verify(self, message):
            events.append("verify")
            return VerificationStatus.VERIFIED

    class FakePipeline:
        def execute(self, context):
            events.append("pipeline")
            return context

    connection = FakeConnection()

    protocol = SMTPProtocol(
        connection,
        hostname="local.onion",
        pipeline=FakePipeline(),
        verifier=FakeVerifier(),
        decryptor=None,
        encryption_private_key=object(),
    )

    protocol.serve()

    assert events == []

    assert any(
        reply.startswith(
            b"554 Transaction failed"
        )
        for reply in connection.sent
    )


def test_smtp_protocol_rejects_e2ee_message_without_private_key():
    events = []

    class FakeConnection:
        def __init__(self):
            self.ip = "127.0.0.1"

            self.lines = iter([
                "EHLO sender.onion",
                "MAIL FROM:<alice@sender.onion>",
                "RCPT TO:<bob@local.onion>",
                "DATA",
                "X-GarlicSMTP-Encryption: fake",
                "",
                "ciphertext",
                ".",
                "QUIT",
            ])

            self.sent = []

        def receive_line(self):
            return next(
                self.lines,
                None,
            )

        def send(self, data):
            self.sent.append(data)

        def close(self):
            pass

    class FakeDecryptor:
        def decrypt(
            self,
            message,
            private_key,
        ):
            events.append("decrypt")

            raise AssertionError(
                "decrypt must not be called "
                "without a private key"
            )

    class FakeVerifier:
        def verify(self, message):
            events.append("verify")
            return VerificationStatus.VERIFIED

    class FakePipeline:
        def execute(self, context):
            events.append("pipeline")
            return context

    connection = FakeConnection()

    protocol = SMTPProtocol(
        connection,
        hostname="local.onion",
        pipeline=FakePipeline(),
        verifier=FakeVerifier(),
        decryptor=FakeDecryptor(),
        encryption_private_key=None,
    )

    protocol.serve()

    assert events == []

    assert any(
        reply.startswith(
            b"554 Transaction failed"
        )
        for reply in connection.sent
    )


def test_smtp_protocol_rejects_malformed_real_e2ee_header():
    events = []

    class FakeConnection:
        def __init__(self):
            self.ip = "127.0.0.1"

            self.lines = iter([
                "EHLO sender.onion",
                "MAIL FROM:<alice@sender.onion>",
                "RCPT TO:<bob@local.onion>",
                "DATA",
                "X-GarlicSMTP-Encryption: malformed",
                "",
                "ciphertext",
                ".",
                "QUIT",
            ])

            self.sent = []

        def receive_line(self):
            return next(
                self.lines,
                None,
            )

        def send(self, data):
            self.sent.append(data)

        def close(self):
            pass

    class FakeVerifier:
        def verify(self, message):
            events.append("verify")
            return VerificationStatus.VERIFIED

    class FakePipeline:
        def execute(self, context):
            events.append("pipeline")
            return context

    recipient_private_key = X25519PrivateKey.generate()

    connection = FakeConnection()

    protocol = SMTPProtocol(
        connection,
        hostname="local.onion",
        pipeline=FakePipeline(),
        verifier=FakeVerifier(),
        decryptor=MessageDecryptor(),
        encryption_private_key=recipient_private_key,
    )

    protocol.serve()

    assert events == []

    assert any(
        reply.startswith(
            b"554 Transaction failed"
        )
        for reply in connection.sent
    )