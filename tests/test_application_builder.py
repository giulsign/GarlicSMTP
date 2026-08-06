from garlicsmtp.application import (
    ApplicationBuilder,
)
from garlicsmtp.configuration import (
    ApplicationPaths,
    ApplicationSettings,
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