# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.core.engine import GarlicSMTP
from pathlib import Path

from garlicsmtp.application import (
    ApplicationBuilder,
)
from garlicsmtp.configuration import (
    ApplicationPaths,
    ApplicationSettings,
)


class FakeRuntime:

    def __init__(self):
        self.started = False
        self.stopped = False

    def start(self):
        self.started = True

    def stop(self):
        self.stopped = True


def test_engine_start_stop():

    runtime = FakeRuntime()

    app = GarlicSMTP(runtime)

    app.start()
    assert runtime.started is True

    app.stop()
    assert runtime.stopped is True


def test_application_uses_context_runtime(
    tmp_path,
):
    context = ApplicationBuilder(
        paths=ApplicationPaths(
            root_dir=tmp_path / "garlicsmtp"
        ),
        settings=ApplicationSettings(),
    ).build()

    app = GarlicSMTP(
        context
    )

    assert app.context is context
    assert app.runtime is context.runtime

    context.queue.backend.close()
    context.store.backend.close()