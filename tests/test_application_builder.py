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