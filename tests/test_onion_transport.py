# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import pytest
from garlicsmtp.queue.factory import QueueFactory
from garlicsmtp.transport.onion.transport import OnionTransport
from garlicsmtp.exceptions import PermanentDeliveryError
from garlicsmtp.security.encryption_capability import (
    EncryptionCapability,
)
from garlicsmtp.exceptions import (
    TemporaryDeliveryError,
)
from garlicsmtp.security.encryption_key_store import (
    MemoryEncryptionKeyStore,
)


class FakeConnection:

    def __init__(self):
        self.socket = object()
        self.closed = False

    def close(self):
        self.closed = True


class FakeSocksClient:

    def __init__(self):
        self.connected = []
        self.connection = FakeConnection()

    def connect(
        self,
        host,
        port,
    ):
        self.connected.append(
            (host, port)
        )

        return self.connection

class FakeSMTPClient:

    def __init__(
        self,
        e2ee_capability=(
            "v=1; alg=x25519; "
            "key=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
        ),
    ):
        self.delivered = []
        self.e2ee_capability = (
            e2ee_capability
        )

    def discover_e2ee_capability(self):
        return self.e2ee_capability

    def deliver(self, message):
        self.delivered.append(
            message
        )

        return True

    

def test_onion_transport_connects_and_delivers(message):

    host = "a" * 56 + ".onion"

    message.envelope.recipients = [
        f"bob@{host}"
    ]

    item = QueueFactory.create(
        message
    )

    socks = FakeSocksClient()
    smtp = FakeSMTPClient()

    transport = OnionTransport(
        socks_client=socks,
        smtp_client_factory=(
            lambda connection: smtp
        ),
    )

    assert transport.deliver(item) is True

    assert socks.connected == [
        (host, 25)
    ]

    assert smtp.delivered == [
        message
    ]

    assert socks.connection.closed is True

def test_onion_transport_reports_discovered_e2ee_capability(
    message,
):
    host = "a" * 56 + ".onion"

    message.envelope.recipients = [
        f"bob@{host}"
    ]

    item = QueueFactory.create(
        message
    )

    socks = FakeSocksClient()
    smtp = FakeSMTPClient()

    discovered = []

    transport = OnionTransport(
        socks_client=socks,
        smtp_client_factory=(
            lambda connection: smtp
        ),
        e2ee_capability_callback=(
            lambda hostname, capability:
            discovered.append(
                (hostname, capability)
            )
        ),
    )

    assert transport.deliver(item) is True

    assert len(discovered) == 1

    discovered_host, capability = (
        discovered[0]
    )

    assert discovered_host == host

    assert isinstance(
        capability,
        EncryptionCapability,
    )

    assert capability.serialize() == (
        "v=1; alg=x25519; "
        "key=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
    )

class ScriptedSocket:

    def __init__(self):
        self.sent = bytearray()
        self.closed = False
        self.timeout = None

        self.responses = bytearray(
            b"220 mail.hidden ready\r\n"
            b"250 mail.hidden\r\n"
            b"250 sender accepted\r\n"
            b"250 recipient accepted\r\n"
            b"250 recipient accepted\r\n"
            b"354 end with dot\r\n"
            b"250 message accepted\r\n"
            b"221 bye\r\n"
        )

    def settimeout(self, timeout):
        self.timeout = timeout

    def sendall(self, data):
        self.sent.extend(data)

    def recv(self, size):
        if not self.responses:
            return b""

        data = bytes(
            self.responses[:size]
        )

        del self.responses[:size]

        return data

    def close(self):
        self.closed = True


class ScriptedSocksConnection:

    def __init__(self):
        self.socket = ScriptedSocket()
        self.closed = False

    def close(self):
        self.socket.close()
        self.closed = True


class ScriptedSocksClient:

    def __init__(self):
        self.connection = ScriptedSocksConnection()
        self.connected = []

    def connect(self, host, port):
        self.connected.append(
            (host, port)
        )

        return self.connection
    

def test_onion_transport_runs_real_smtp_client(message):

    host = "a" * 56 + ".onion"

    message.envelope.sender = (
        "alice@sender.onion"
    )

    message.envelope.recipients = [
        f"bob@{host}",
        f"carol@{host}",
    ]

    message.headers.fields[
        "Subject"
    ] = "Tor delivery test"

    message.body = "Hello over Tor"

    item = QueueFactory.create(
        message
    )

    socks = ScriptedSocksClient()

    transport = OnionTransport(
        socks_client=socks,
    )

    assert transport.deliver(item) is True

    assert socks.connected == [
        (host, 25)
    ]

    sent = bytes(
        socks.connection.socket.sent
    ).decode("utf-8")

    assert sent == (
        "EHLO [127.0.0.1]\r\n"
        "MAIL FROM:<alice@sender.onion>\r\n"
        f"RCPT TO:<bob@{host}>\r\n"
        f"RCPT TO:<carol@{host}>\r\n"
        "DATA\r\n"
        "Subject: Tor delivery test\r\n"
        "\r\n"
        "Hello over Tor\r\n"
        ".\r\n"
        "QUIT\r\n"
    )

    assert socks.connection.closed is True


import pytest

from garlicsmtp.exceptions import PermanentDeliveryError


def test_onion_transport_rejects_recipients_on_different_hosts(
    message,
):
    first_host = "a" * 56 + ".onion"
    second_host = "b" * 56 + ".onion"

    message.envelope.recipients = [
        f"bob@{first_host}",
        f"carol@{second_host}",
    ]

    item = QueueFactory.create(
        message
    )

    socks = FakeSocksClient()
    smtp = FakeSMTPClient()

    transport = OnionTransport(
        socks_client=socks,
        smtp_client_factory=(
            lambda connection: smtp
        ),
    )

    with pytest.raises(
        PermanentDeliveryError,
        match="different onion hosts",
    ):
        transport.deliver(item)

    assert socks.connected == []
    assert smtp.delivered == []


def test_onion_transport_does_not_report_missing_e2ee_capability(
    message,
):
    host = "a" * 56 + ".onion"

    message.envelope.recipients = [
        f"bob@{host}"
    ]

    item = QueueFactory.create(
        message
    )

    socks = FakeSocksClient()

    smtp = FakeSMTPClient(
        e2ee_capability=None,
    )

    discovered = []

    transport = OnionTransport(
        socks_client=socks,
        smtp_client_factory=(
            lambda connection: smtp
        ),
        e2ee_capability_callback=(
            lambda hostname, capability:
            discovered.append(
                (hostname, capability)
            )
        ),
    )

    assert transport.deliver(item) is True

    assert discovered == []


def test_onion_transport_reports_parsed_e2ee_capability(
    message,
):
    host = "a" * 56 + ".onion"

    message.envelope.recipients = [
        f"bob@{host}"
    ]

    item = QueueFactory.create(
        message
    )

    socks = FakeSocksClient()
    smtp = FakeSMTPClient()

    discovered = []

    transport = OnionTransport(
        socks_client=socks,
        smtp_client_factory=(
            lambda connection: smtp
        ),
        e2ee_capability_callback=(
            lambda hostname, capability:
            discovered.append(
                (hostname, capability)
            )
        ),
    )

    assert transport.deliver(item) is True

    assert len(discovered) == 1

    discovered_host, capability = (
        discovered[0]
    )

    assert discovered_host == host

    assert isinstance(
        capability,
        EncryptionCapability,
    )

    assert capability.serialize() == (
        "v=1; alg=x25519; "
        "key=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
    )


def test_onion_transport_treats_invalid_e2ee_capability_as_temporary_error(
    message,
):
    host = "a" * 56 + ".onion"

    message.envelope.recipients = [
        f"bob@{host}"
    ]

    item = QueueFactory.create(
        message
    )

    socks = FakeSocksClient()

    smtp = FakeSMTPClient(
        e2ee_capability=(
            "v=1; alg=x25519; key=dGVzdA=="
        ),
    )

    transport = OnionTransport(
        socks_client=socks,
        smtp_client_factory=(
            lambda connection: smtp
        ),
    )

    with pytest.raises(
        TemporaryDeliveryError,
        match="Invalid E2EE capability",
    ):
        transport.deliver(item)


def test_onion_transport_discovered_key_can_be_pinned(
    message,
):
    host = "a" * 56 + ".onion"

    message.envelope.recipients = [
        f"bob@{host}"
    ]

    item = QueueFactory.create(
        message
    )

    socks = FakeSocksClient()
    smtp = FakeSMTPClient()

    store = MemoryEncryptionKeyStore()

    def remember_capability(
        hostname,
        capability,
    ):
        store.remember(
            hostname,
            capability.public_key.public_bytes_raw(),
        )

    transport = OnionTransport(
        socks_client=socks,
        smtp_client_factory=(
            lambda connection: smtp
        ),
        e2ee_capability_callback=(
            remember_capability
        ),
    )

    assert transport.deliver(item) is True

    assert store.get(host) == (
        b"\x00" * 32
    )


def test_onion_transport_treats_e2ee_key_change_as_temporary_error(
    message,
):
    host = "a" * 56 + ".onion"

    message.envelope.recipients = [
        f"bob@{host}"
    ]
    
    def reject_changed_key(
        hostname,
        capability,
    ):
        raise ValueError(
            "encryption key changed"
        )

    socks_client = FakeSocksClient()

    smtp_client = FakeSMTPClient(
        e2ee_capability=(
            "v=1; alg=x25519; "
            "key=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
        )
    )

    transport = OnionTransport(
        socks_client=socks_client,
        smtp_client_factory=lambda connection: smtp_client,
        e2ee_capability_callback=reject_changed_key,
    )

    item = QueueFactory.create(
        message
    )

    with pytest.raises(
        TemporaryDeliveryError,
        match="E2EE key rejected",
    ):
        transport.deliver(item)

    assert socks_client.connection.closed is True


def test_onion_transport_discovers_e2ee_before_delivering(
    message,
):
    host = "a" * 56 + ".onion"

    message.envelope.recipients = [
        f"bob@{host}"
    ]

    item = QueueFactory.create(
        message
    )

    socks = FakeSocksClient()
    events = []

    class DiscoverySMTPClient:

        e2ee_capability = None

        def discover_e2ee_capability(self):
            events.append("discover")

            self.e2ee_capability = (
                "v=1; alg=x25519; "
                "key=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
            )

            return self.e2ee_capability

        def deliver(self, message):
            events.append("deliver")
            return True

    smtp = DiscoverySMTPClient()

    transport = OnionTransport(
        socks_client=socks,
        smtp_client_factory=(
            lambda connection: smtp
        ),
    )

    assert transport.deliver(item) is True

    assert events == [
        "discover",
        "deliver",
    ]


def test_onion_transport_rejects_changed_key_before_smtp_envelope(
    message,
):
    host = "a" * 56 + ".onion"

    message.envelope.sender = (
        "alice@sender.onion"
    )

    message.envelope.recipients = [
        f"bob@{host}"
    ]

    message.body = "must not be sent"

    item = QueueFactory.create(
        message
    )

    socks = ScriptedSocksClient()

    socks.connection.socket.responses = bytearray(
        (
            "220 mail.hidden ready\r\n"
            "250-mail.hidden\r\n"
            "250 GARLICSMTP-E2EE "
            "v=1; alg=x25519; "
            "key=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=\r\n"
        ).encode("ascii")
    )

    def reject_changed_key(
        hostname,
        capability,
    ):
        raise ValueError(
            "encryption key changed"
        )

    transport = OnionTransport(
        socks_client=socks,
        e2ee_capability_callback=(
            reject_changed_key
        ),
    )

    with pytest.raises(
        TemporaryDeliveryError,
        match="E2EE key rejected",
    ):
        transport.deliver(item)

    sent = bytes(
        socks.connection.socket.sent
    ).decode("utf-8")

    assert sent == (
        "EHLO [127.0.0.1]\r\n"
    )

    assert "MAIL FROM:" not in sent
    assert "RCPT TO:" not in sent
    assert "DATA\r\n" not in sent
    assert "must not be sent" not in sent

    assert (
        socks.connection.closed
        is True
    )


def test_onion_transport_can_discover_e2ee_without_delivering(
    message,
):
    host = "a" * 56 + ".onion"

    message.envelope.recipients = [
        f"bob@{host}"
    ]

    socks = FakeSocksClient()
    smtp = FakeSMTPClient()

    discovered = []

    transport = OnionTransport(
        socks_client=socks,
        smtp_client_factory=(
            lambda connection: smtp
        ),
        e2ee_capability_callback=(
            lambda hostname, capability:
            discovered.append(
                (hostname, capability)
            )
        ),
    )

    capability = (
        transport.discover_e2ee_capability(
            host
        )
    )

    assert isinstance(
        capability,
        EncryptionCapability,
    )

    assert capability.serialize() == (
        "v=1; alg=x25519; "
        "key=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
    )

    assert len(discovered) == 1

    discovered_host, discovered_capability = (
        discovered[0]
    )

    assert discovered_host == host

    assert (
        discovered_capability.serialize()
        == capability.serialize()
    )

    assert smtp.delivered == []

    assert socks.connected == [
        (host, 25)
    ]

    assert socks.connection.closed is True


def test_onion_transport_deliver_uses_discovery_before_delivery(
    message,
):
    host = "a" * 56 + ".onion"

    message.envelope.recipients = [
        f"bob@{host}"
    ]

    events = []

    class OrderedSMTPClient(
        FakeSMTPClient
    ):
        def discover_e2ee_capability(self):
            events.append("discover")
            return super().discover_e2ee_capability()

        def deliver(self, message):
            events.append("deliver")
            return super().deliver(message)

    socks = FakeSocksClient()
    smtp = OrderedSMTPClient()

    transport = OnionTransport(
        socks_client=socks,
        smtp_client_factory=(
            lambda connection: smtp
        ),
    )

    assert transport.deliver(
        QueueFactory.create(message)
    ) is True

    assert events == [
        "discover",
        "deliver",
    ]