# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from garlicsmtp.application.context import (
        ApplicationContext,
    )
    from garlicsmtp.core.engine.runtime import (
        Runtime,
    )


class GarlicSMTP:

    def __init__(
        self,
        context: (
            "ApplicationContext | Runtime | Any | None"
        ) = None,
        *,
        runtime: "Runtime | Any | None" = None,
    ):
        target = (
            runtime
            if runtime is not None
            else context
        )

        if target is None:
            raise ValueError(
                "GarlicSMTP requires an "
                "application context or runtime"
            )

        if hasattr(
            target,
            "runtime",
        ):
            self.context = target
            self.runtime = target.runtime
        else:
            self.context = None
            self.runtime = target

    def start(self) -> None:
        self.runtime.start()

    def run(self) -> None:
        self.runtime.run()

    def stop(self) -> None:
        self.runtime.stop()