# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import threading
from garlicsmtp.application.context import (
    ApplicationContext,
)
from garlicsmtp.application.status import (
    ApplicationStatus,
)
from garlicsmtp.application.status_provider import (
    ApplicationStatusProvider,
)
from garlicsmtp.application.event import (
    ApplicationEventSource,
)


class ApplicationController:

    def __init__(
        self,
        context: ApplicationContext,
    ) -> None:
        self.context = context

        self.status_provider = (
            ApplicationStatusProvider(
                context
            )
        )

        self._runtime_thread: (
            threading.Thread | None
        ) = None

        self._runtime_thread_lock = (
            threading.RLock()
        )

    def start(
        self,
    ) -> ApplicationStatus:
        self.context.runtime.start()
        self._start_runtime_loop()

        self.context.event_service.info(
            ApplicationEventSource.APPLICATION,
            "Application started",
        )

        return self.status()


    def stop(
        self,
    ) -> ApplicationStatus:
        self.context.runtime.stop()
        self._stop_runtime_loop()

        self.context.event_service.info(
            ApplicationEventSource.APPLICATION,
            "Application stopped",
        )

        return self.status()


    def restart(
        self,
    ) -> ApplicationStatus:
        self.context.runtime.stop()
        self._stop_runtime_loop()

        self.context.runtime.start()
        self._start_runtime_loop()

        self.context.event_service.info(
            ApplicationEventSource.APPLICATION,
            "Application restarted",
        )

        return self.status()


    def status(
        self,
    ) -> ApplicationStatus:
        return self.status_provider.snapshot()

    def subscribe(
        self,
        listener,
    ) -> None:
        self.context.event_hub.subscribe(
            listener
        )


    def unsubscribe(
        self,
        listener,
    ) -> None:
        self.context.event_hub.unsubscribe(
            listener
        )

    def _start_runtime_loop(
        self,
    ) -> None:
        with self._runtime_thread_lock:
            if (
                self._runtime_thread is not None
                and self._runtime_thread.is_alive()
            ):
                return

            self._runtime_thread = threading.Thread(
                target=self.context.runtime.run,
                daemon=True,
                name="garlicsmtp-runtime",
            )

            self._runtime_thread.start()


    def _stop_runtime_loop(
        self,
    ) -> None:
        with self._runtime_thread_lock:
            thread = self._runtime_thread

        if thread is None:
            return

        thread.join(
            timeout=3
        )

        with self._runtime_thread_lock:
            if self._runtime_thread is thread:
                self._runtime_thread = None
