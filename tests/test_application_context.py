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


def test_application_context_holds_dependencies(
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

    assert context.logger is not None
    assert context.store is not None
    assert context.queue is not None
    assert context.transport is not None
    assert context.pipeline is not None

    assert context.smtp_server is not None
    assert context.imap_server is not None
    assert context.queue_worker is not None
    assert context.runtime is not None

    assert (
        context.smtp_server.pipeline
        is context.pipeline
    )

    assert (
        context.imap_server.store
        is context.store
    )

    assert (
        context.queue_worker.queue
        is context.queue
    )

    assert (
        context.queue_worker.transport
        is context.transport
    )

    context.queue.backend.close()
    context.store.backend.close()