# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import time

from garlicsmtp.core.engine.state import RuntimeState
from garlicsmtp.logger import Logger


class Runtime:

    def __init__(
        self,
        services=None,
        tasks=None,
        logger=None,
    ):
        self.services = services or []
        self.tasks = tasks or []
        self.logger = logger or Logger()
        self.state = RuntimeState.STOPPED

    def start(self) -> None:
        self.logger.info(
            "Runtime starting..."
        )

        self.state = RuntimeState.STARTING

        started = []

        try:
            for service in self.services:
                service.start()
                started.append(
                    service
                )

            self.state = RuntimeState.RUNNING

            self.logger.info(
                "Runtime ready"
            )

        except Exception:
            for service in reversed(
                started
            ):
                try:
                    service.stop()
                except Exception:
                    pass

            self.state = RuntimeState.STOPPED

            raise

    def stop(self) -> None:
        if self.state is RuntimeState.STOPPED:
            return

        self.logger.info(
            "Runtime stopping..."
        )

        self.state = RuntimeState.STOPPING

        for service in reversed(
            self.services
        ):
            try:
                service.stop()
            except Exception:
                pass

        self.state = RuntimeState.STOPPED

        self.logger.info(
            "Runtime stopped"
        )

    def run(self) -> None:
        try:
            while (
                self.state
                is RuntimeState.RUNNING
            ):
                for task in self.tasks:
                    task.tick()

                time.sleep(1)

        except KeyboardInterrupt:
            self.stop()