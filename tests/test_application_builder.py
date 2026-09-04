# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.application import (
    ApplicationBuilder,
)
from garlicsmtp.configuration import (
    ApplicationPaths,
    ApplicationSettings,
)
from garlicsmtp.tor.onion_service_manager import (
    OnionServiceManager,
)
from garlicsmtp.security.trust_store import (
    FileTrustStore,
)
from garlicsmtp.security.verifier import (
    Ed25519MessageVerifier,
)
from cryptography.hazmat.primitives import (
    serialization,
)
from garlicsmtp.security.encryption_capability import (
    EncryptionCapability,
)
from garlicsmtp.security.encryption_identity import (
    EncryptionIdentity,
)
from garlicsmtp.security.encryption_key_store import (
    FileEncryptionKeyStore,
)
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
)

from garlicsmtp.core.pipeline import (
    PipelineContext,
)

from garlicsmtp.security.decryptor import (
    MessageDecryptor,
)

from garlicsmtp.security.encryptor import (
    ENCRYPTION_HEADER,
)
import sqlite3
from garlicsmtp.transport.onion.transport import (
    OnionTransport,
)
import sqlite3

from garlicsmtp.security.encryption_capability import (
    EncryptionCapability,
)
from garlicsmtp.security.decryptor import (
    MessageDecryptor,
)
from garlicsmtp.security.encryptor import (
    ENCRYPTION_HEADER,
)


def test_application_builder_creates_context(
    tmp_path,
):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp"
    )

    settings = ApplicationSettings()

    context = ApplicationBuilder(
        paths=paths,
        settings=settings,
    ).build()

    assert context.paths is paths
    assert context.settings is settings

    assert (
        context.paths.mailbox_database.exists()
    )

    assert (
        context.paths.queue_database.exists()
    )

    assert context.store is not None
    assert context.queue is not None
    assert context.transport is not None
    assert context.pipeline is not None



def test_application_builder_uses_persistent_backends(
    tmp_path,
    message,
):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp"
    )

    first = ApplicationBuilder(
        paths=paths,
        settings=ApplicationSettings(),
    ).build()

    first.store.save(
        "bob@test.onion",
        message,
    )

    first.queue.backend.close()
    first.store.backend.close()

    second = ApplicationBuilder(
        paths=paths,
        settings=ApplicationSettings(),
    ).build()

    assert second.store.count(
        "bob@test.onion"
    ) == 1

    second.queue.backend.close()
    second.store.backend.close()



def test_application_builder_loads_settings(
    tmp_path,
):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp"
    )

    paths.create_directories()

    paths.settings_file.write_text(
        """
hostname = "mail.example.onion"
local_domain = "example.onion"

[tor]
socks_host = "127.0.0.2"
socks_port = 9150
""".strip(),
        encoding="utf-8",
    )

    context = ApplicationBuilder(
        paths=paths
    ).build()

    assert context.settings.hostname == (
        "mail.example.onion"
    )

    assert context.settings.local_domain == (
        "example.onion"
    )

    assert context.settings.tor.socks_port == 9150

    context.queue.backend.close()
    context.store.backend.close()


def test_application_builder_connects_runtime_services(
    tmp_path,
):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp"
    )

    context = ApplicationBuilder(
        paths=paths,
        settings=ApplicationSettings(),
    ).build()

    assert context.runtime.services == [
        context.smtp_server,
        context.onion_service,
        context.imap_server,
        context.queue_worker,
        context.tor_monitor,
    ]

    assert context.runtime.tasks == [   
        context.smtp_server,
        context.imap_server,
        context.queue_worker,
        context.tor_monitor,
    ]

    assert (
        context.runtime.logger
        is context.logger
    )

    context.queue.backend.close()
    context.store.backend.close()

def test_application_builder_uses_development_paths():
    builder = ApplicationBuilder()

    assert (
        builder.paths.settings_file.name
        == "default.toml"
    )

    assert (
        builder.paths.settings_file
        .parent
        .name
        == "config"
    )

    assert (
        builder.paths.settings_file
        .exists()
    )


def test_application_builder_preserves_explicit_paths(
    tmp_path,
):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp"
    )

    builder = ApplicationBuilder(
        paths=paths,
        settings=ApplicationSettings(),
    )

    assert builder.paths is paths

    assert builder.paths.settings_file == (
        tmp_path
        / "garlicsmtp"
        / "config"
        / "settings.toml"
    )

from garlicsmtp.application.builder import (
    ApplicationBuilder,
)


class FakeService:

    def __init__(
        self,
        name,
    ):
        self.name = name


def test_application_builder_puts_onion_service_after_smtp():
    smtp_server = FakeService(
        "smtp"
    )
    imap_server = FakeService(
        "imap"
    )
    queue_worker = FakeService(
        "queue"
    )
    onion_service = FakeService(
        "onion"
    )
    tor_monitor = FakeService(
        "tor_monitor"
    )

    runtime = ApplicationBuilder._build_runtime(
        smtp_server=smtp_server,
        imap_server=imap_server,
        queue_worker=queue_worker,
        onion_service=onion_service,
        tor_monitor=tor_monitor,
        logger=None,
    )

    assert runtime.services == [
        smtp_server,
        onion_service,
        imap_server,
        queue_worker,
        tor_monitor,
    ]


def test_application_builder_builds_onion_service(
    tmp_path,
):
    paths = ApplicationPaths.for_user(
        home=tmp_path
    )

    settings = ApplicationSettings()

    settings.tor.control_enabled = True

    builder = ApplicationBuilder(
        paths=paths,
        settings=settings,
    )

    onion_service = (
        builder._build_onion_service(
            settings
        )
    )

    assert isinstance(
        onion_service,
        OnionServiceManager,
    )

    assert (
        onion_service.identity_file
        == paths.onion_identity_file
    )

    assert onion_service.virtual_port == (
        settings.tor.onion_smtp_port
    )

    assert onion_service.target_host == (
        settings.smtp.host
    )

    assert onion_service.target_port == (
        settings.smtp.port
    )


def test_application_builder_disables_onion_service_when_tor_disabled(
    tmp_path,
):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp"
    )

    settings = ApplicationSettings()

    settings.tor.enabled = False

    context = ApplicationBuilder(
        paths=paths,
        settings=settings,
    ).build()

    assert context.onion_service is None

    assert context.runtime.services == [
        context.smtp_server,
        context.imap_server,
        context.queue_worker,
        context.tor_monitor,
    ]


def test_application_builder_connects_onion_hostname_to_tor_status(
    tmp_path,
):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp"
    )

    settings = ApplicationSettings()
    settings.tor.enabled = True

    builder = ApplicationBuilder(
        paths=paths,
        settings=settings,
    )

    onion_service = (
        builder._build_onion_service(
            settings
        )
    )

    onion_service.hostname = (
        ("a" * 56)
        + ".onion"
    )

    provider = (
        builder._build_tor_status_provider(
            settings,
            onion_service=onion_service,
        )
    )

    status = provider.initial_status()

    assert status.onion_hostname == (
        ("a" * 56)
        + ".onion"
    )


def test_application_builder_trusts_local_onion_sender_key(
    tmp_path,
):
    paths = ApplicationPaths(
        root_dir=tmp_path,
    )

    settings = ApplicationSettings()
    settings.tor.enabled = True

    context = ApplicationBuilder(
        paths=paths,
        settings=settings,
    ).build()

    onion_service = context.onion_service

    hostname = (
        ("a" * 56)
        + ".onion"
    )

    assert onion_service is not None
    assert (
        onion_service.hostname_callback
        is not None
    )

    onion_service.hostname_callback(
        hostname
    )

    public_key = (
        context.signer.private_key
        .public_key()
        .public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
    )

    assert (
        context.verifier
        .trust_store
        .is_trusted(
            "garlicsmtp@" + hostname,
            public_key,
        )
    )


def test_application_builder_wires_trust_aware_verifier_into_smtp_server(
    tmp_path,
):
    paths = ApplicationPaths(
        root_dir=tmp_path,
    )

    context = ApplicationBuilder(
        paths=paths,
        settings=ApplicationSettings(),
    ).build()

    verifier = context.smtp_server.verifier

    assert isinstance(
        verifier,
        Ed25519MessageVerifier,
    )

    assert isinstance(
        verifier.trust_store,
        FileTrustStore,
    )

    assert (
        verifier.trust_store.path
        == tmp_path / "trusted_keys.json"
    )


def test_application_builder_preserves_trusted_key_across_builds(
    tmp_path,
):
    paths = ApplicationPaths(
        root_dir=tmp_path,
    )

    first_context = ApplicationBuilder(
        paths=paths,
        settings=ApplicationSettings(),
    ).build()

    first_store = (
        first_context.smtp_server
        .verifier
        .trust_store
    )

    sender = "alice@sender.onion"
    public_key = b"a" * 32

    first_store.trust(
        sender,
        public_key,
    )

    second_context = ApplicationBuilder(
        paths=paths,
        settings=ApplicationSettings(),
    ).build()

    second_store = (
        second_context.smtp_server
        .verifier
        .trust_store
    )

    assert second_store.is_trusted(
        sender,
        public_key,
    )


def test_application_builder_configures_e2ee_capability(
    tmp_path,
):
    paths = ApplicationPaths(
        root_dir=tmp_path / "garlicsmtp"
    )

    settings = ApplicationSettings()
    settings.tor.enabled = False

    context = ApplicationBuilder(
        paths=paths,
        settings=settings,
    ).build()

    identity = EncryptionIdentity(
        paths.root_dir / "encryption.key"
    )

    capability = EncryptionCapability.parse(
        context.smtp_server.e2ee_capability
    )

    assert (
        capability.public_key.public_bytes_raw()
        == identity.private_key
        .public_key()
        .public_bytes_raw()
    )

    context.queue.backend.close()
    context.store.backend.close()


def test_application_builder_builds_persistent_encryption_key_store(
    tmp_path,
):
    paths = ApplicationPaths(
        root_dir=tmp_path,
    )

    context = ApplicationBuilder(
        paths=paths,
        settings=ApplicationSettings(),
    ).build()

    assert isinstance(
        context.encryption_key_store,
        FileEncryptionKeyStore,
    )

    assert (
        context.encryption_key_store.path
        == tmp_path / "encryption_keys.json"
    )

    context.queue.backend.close()


def test_application_builder_pins_discovered_e2ee_key(
    tmp_path,
):
    paths = ApplicationPaths(
        root_dir=tmp_path,
    )

    context = ApplicationBuilder(
        paths=paths,
        settings=ApplicationSettings(),
    ).build()

    onion_transport = (
        context.transport.default_transport
    )

    host = "a" * 56 + ".onion"

    capability = EncryptionCapability.parse(
        (
            "v=1; alg=x25519; "
            "key=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
        )
    )

    assert (
        onion_transport.e2ee_capability_callback
        is not None
    )

    onion_transport.e2ee_capability_callback(
        host,
        capability,
    )

    assert (
        context.encryption_key_store.get(host)
        == b"\x00" * 32
    )

    context.queue.backend.close()


def test_application_builder_wires_remote_encryption_before_queue(
        tmp_path,
        message,
    ):
        paths = ApplicationPaths(
            root_dir=tmp_path,
        )

        settings = ApplicationSettings()
        settings.tor.enabled = False

        context = ApplicationBuilder(
            paths=paths,
            settings=settings,
        ).build()

        host = "b" * 56 + ".onion"

        message.envelope.recipients = [
            f"bob@{host}"
        ]

        message.headers.add(
            "Subject",
            "Builder secret",
        )

        message.body = (
            "BUILDER-QUEUE-PLAINTEXT-SENTINEL"
        )

        recipient_private_key = (
            X25519PrivateKey.generate()
        )

        context.encryption_key_store.remember(
            host,
            recipient_private_key
            .public_key()
            .public_bytes_raw(),
        )

        try:
            result = context.pipeline.execute(
                PipelineContext(
                    message=message,
                )
            )

            assert result.accepted is True
            assert context.queue.size() == 1

            item = context.queue.dequeue()
            encrypted = item.message

            assert (
                encrypted.headers.get(
                    ENCRYPTION_HEADER
                )
                is not None
            )

            assert (
                "BUILDER-QUEUE-PLAINTEXT-SENTINEL"
                not in encrypted.body
            )

            decrypted = MessageDecryptor().decrypt(
                encrypted,
                recipient_private_key,
            )

            assert decrypted.body == (
                "BUILDER-QUEUE-PLAINTEXT-SENTINEL"
            )

            assert decrypted.headers.get(
                "Subject"
            ) == "Builder secret"

        finally:
            context.queue.backend.close()
            context.store.backend.close()


def test_application_queue_persists_remote_message_as_ciphertext(
    tmp_path,
    message,
):
    paths = ApplicationPaths(
        root_dir=tmp_path,
    )

    settings = ApplicationSettings()
    settings.tor.enabled = False

    context = ApplicationBuilder(
        paths=paths,
        settings=settings,
    ).build()

    host = "c" * 56 + ".onion"

    message.envelope.recipients = [
        f"bob@{host}"
    ]

    message.headers.add(
        "Subject",
        "SQLite secret",
    )

    sentinel = (
        "SQLITE-QUEUE-PLAINTEXT-SENTINEL"
    )

    message.body = sentinel

    recipient_private_key = (
        X25519PrivateKey.generate()
    )

    context.encryption_key_store.remember(
        host,
        recipient_private_key
        .public_key()
        .public_bytes_raw(),
    )

    try:
        result = context.pipeline.execute(
            PipelineContext(
                message=message,
            )
        )

        assert result.accepted is True
        assert context.queue.size() == 1

        connection = sqlite3.connect(
            paths.queue_database
        )

        try:
            row = connection.execute(
                """
                SELECT payload
                FROM queue_items
                """
            ).fetchone()
        finally:
            connection.close()

        assert row is not None

        payload = row[0]

        assert sentinel not in payload
        assert "SQLite secret" not in payload

        restored = context.queue.peek()

        assert restored is not None

        assert (
            restored.message.headers.get(
                ENCRYPTION_HEADER
            )
            is not None
        )

        decrypted = MessageDecryptor().decrypt(
            restored.message,
            recipient_private_key,
        )

        assert decrypted.body == sentinel

        assert decrypted.headers.get(
            "Subject"
        ) == "SQLite secret"

    finally:
        context.queue.backend.close()
        context.store.backend.close()


def test_application_builder_wires_first_contact_discovery_before_queue(
    tmp_path,
    message,
):
    paths = ApplicationPaths(
        root_dir=tmp_path,
    )

    settings = ApplicationSettings()
    settings.tor.enabled = False

    host = "d" * 56 + ".onion"

    recipient_private_key = (
        X25519PrivateKey.generate()
    )

    class DiscoveryTransport:
        def __init__(self):
            self.discovered = []
            self.key_store = None

        def discover_e2ee_capability(
            self,
            hostname,
        ):
            self.discovered.append(
                hostname
            )

            self.key_store.remember(
                hostname,
                recipient_private_key
                .public_key()
                .public_bytes_raw(),
            )

        def deliver(self, item):
            raise AssertionError(
                "delivery must not happen "
                "during enqueue"
            )

    transport = DiscoveryTransport()

    context = ApplicationBuilder(
        paths=paths,
        settings=settings,
        default_transport=transport,
    ).build()

    transport.key_store = (
        context.encryption_key_store
    )

    message.envelope.recipients = [
        f"bob@{host}"
    ]

    sentinel = (
        "FIRST-CONTACT-BUILDER-SENTINEL"
    )

    message.body = sentinel

    try:
        result = context.pipeline.execute(
            PipelineContext(
                message=message,
            )
        )

        assert result.accepted is True

        assert transport.discovered == [
            host
        ]

        assert context.queue.size() == 1

        item = context.queue.peek()

        assert item is not None
        assert sentinel not in item.message.body

        decrypted = MessageDecryptor().decrypt(
            item.message,
            recipient_private_key,
        )

        assert decrypted.body == sentinel

    finally:
        context.queue.backend.close()
        context.store.backend.close()


def test_application_builder_first_contact_pins_discovered_onion_key(
    tmp_path,
):
    paths = ApplicationPaths(
        root_dir=tmp_path,
    )

    settings = ApplicationSettings()
    settings.tor.enabled = False

    host = "e" * 56 + ".onion"

    recipient_private_key = (
        X25519PrivateKey.generate()
    )

    capability = EncryptionCapability(
        public_key=(
            recipient_private_key
            .public_key()
        )
    ).serialize()

    class FakeConnection:
        def __init__(self):
            self.socket = object()
            self.closed = False

        def close(self):
            self.closed = True

    class FakeSocksClient:
        def __init__(self):
            self.connection = (
                FakeConnection()
            )
            self.connected = []

        def connect(
            self,
            hostname,
            port,
        ):
            self.connected.append(
                (hostname, port)
            )

            return self.connection

    class FakeSMTPClient:
        def discover_e2ee_capability(
            self,
        ):
            return capability

        def deliver(
            self,
            message,
        ):
            raise AssertionError(
                "first-contact discovery "
                "must not deliver"
            )

    socks = FakeSocksClient()

    onion = OnionTransport(
        socks_client=socks,
        smtp_client_factory=(
            lambda connection:
            FakeSMTPClient()
        ),
    )

    context = ApplicationBuilder(
        paths=paths,
        settings=settings,
        default_transport=onion,
    ).build()

    try:
        assert (
            context.encryption_key_store.get(
                host
            )
            is None
        )

        onion.discover_e2ee_capability(
            host
        )

        assert (
            context.encryption_key_store.get(
                host
            )
            == recipient_private_key
            .public_key()
            .public_bytes_raw()
        )

        assert socks.connected == [
            (host, 25)
        ]

        assert (
            socks.connection.closed
            is True
        )

    finally:
        context.queue.backend.close()
        context.store.backend.close()


def test_application_builder_first_contact_persists_ciphertext(
    tmp_path,
    message,
):
    paths = ApplicationPaths(
        root_dir=tmp_path,
    )

    settings = ApplicationSettings()
    settings.tor.enabled = False

    host = "f" * 56 + ".onion"

    recipient_private_key = (
        X25519PrivateKey.generate()
    )

    capability = EncryptionCapability(
        public_key=(
            recipient_private_key
            .public_key()
        )
    ).serialize()

    class FakeConnection:
        def __init__(self):
            self.socket = object()
            self.closed = False

        def close(self):
            self.closed = True

    class FakeSocksClient:
        def __init__(self):
            self.connection = (
                FakeConnection()
            )
            self.connected = []

        def connect(
            self,
            hostname,
            port,
        ):
            self.connected.append(
                (hostname, port)
            )
            return self.connection

    class FakeSMTPClient:
        def discover_e2ee_capability(
            self,
        ):
            return capability

        def deliver(
            self,
            message,
        ):
            raise AssertionError(
                "message must only be queued "
                "during pipeline processing"
            )

    socks = FakeSocksClient()

    onion = OnionTransport(
        socks_client=socks,
        smtp_client_factory=(
            lambda connection:
            FakeSMTPClient()
        ),
    )

    context = ApplicationBuilder(
        paths=paths,
        settings=settings,
        default_transport=onion,
    ).build()

    try:
        message.envelope.recipients = [
            f"bob@{host}"
        ]

        message.headers.fields[
            "Subject"
        ] = "FIRST-CONTACT-SUBJECT"

        message.body = (
            "FIRST-CONTACT-PLAINTEXT-SENTINEL"
        )

        result = context.pipeline.execute(
            PipelineContext(
                message=message,
            )
        )

        assert result.accepted is True

        assert (
            context.encryption_key_store.get(
                host
            )
            == recipient_private_key
            .public_key()
            .public_bytes_raw()
        )

        assert socks.connected == [
            (host, 25)
        ]

        assert (
            socks.connection.closed
            is True
        )

        connection = sqlite3.connect(
            paths.queue_database
        )

        try:
            row = connection.execute(
                """
                SELECT payload
                FROM queue_items
                """
            ).fetchone()
        finally:
            connection.close()

        assert row is not None

        payload = row[0]

        assert (
            "FIRST-CONTACT-PLAINTEXT-SENTINEL"
            not in payload
        )

        assert (
            "FIRST-CONTACT-SUBJECT"
            not in payload
        )

        item = context.queue.peek()

        assert item is not None

        assert (
            item.message.headers.get(
                ENCRYPTION_HEADER
            )
            is not None
        )

        decrypted = MessageDecryptor().decrypt(
            item.message,
            recipient_private_key,
        )

        assert decrypted.body == (
            "FIRST-CONTACT-PLAINTEXT-SENTINEL"
        )

        assert (
            decrypted.headers.get(
                "Subject"
            )
            == "FIRST-CONTACT-SUBJECT"
        )

    finally:
        context.queue.backend.close()
        context.store.backend.close()


