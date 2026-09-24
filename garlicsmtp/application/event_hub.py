# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import inspect
import threading
from collections.abc import Callable

from garlicsmtp.application.event import (
    ApplicationEvent,
)


ApplicationEventListener = Callable[
    ...,
    None,
]


class ApplicationEventHub:

    def __init__(
        self,
    ) -> None:
        self._listeners: list[
            ApplicationEventListener
        ] = []

        self._lock = threading.RLock()

    def subscribe(
        self,
        listener: ApplicationEventListener,
    ) -> None:
        with self._lock:
            if listener not in self._listeners:
                self._listeners.append(
                    listener
                )

    def unsubscribe(
        self,
        listener: ApplicationEventListener,
    ) -> None:
        with self._lock:
            if listener in self._listeners:
                self._listeners.remove(
                    listener
                )

    def publish(
        self,
        event: ApplicationEvent | None = None,
    ) -> None:
        with self._lock:
            listeners = tuple(
                self._listeners
            )

        for listener in listeners:
            self._notify(
                listener,
                event,
            )

    @staticmethod
    def _notify(
        listener: ApplicationEventListener,
        event: ApplicationEvent | None,
    ) -> None:
        try:
            signature = inspect.signature(
                listener
            )
        except (
            TypeError,
            ValueError,
        ):
            listener()
            return

        accepts_event = any(
            parameter.kind
            in {
                inspect.Parameter
                .POSITIONAL_ONLY,
                inspect.Parameter
                .POSITIONAL_OR_KEYWORD,
                inspect.Parameter
                .VAR_POSITIONAL,
            }
            for parameter in (
                signature.parameters.values()
            )
        )

        if accepts_event:
            listener(
                event
            )
        else:
            listener()