# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import threading

from garlicsmtp.storage.event_sink import (
    StoreEventSink,
)


class CompositeStoreEventSink(
    StoreEventSink
):

    def __init__(self) -> None:
        self._sinks: list[StoreEventSink] = []
        self._lock = threading.RLock()

    def add(
        self,
        sink: StoreEventSink,
    ) -> None:
        with self._lock:
            if sink not in self._sinks:
                self._sinks.append(
                    sink
                )

    def remove(
        self,
        sink: StoreEventSink,
    ) -> None:
        with self._lock:
            if sink in self._sinks:
                self._sinks.remove(
                    sink
                )

    def _snapshot(
        self,
    ) -> tuple[StoreEventSink, ...]:
        with self._lock:
            return tuple(
                self._sinks
            )

    def message_added(
        self,
        mailbox: str,
    ) -> None:
        for sink in self._snapshot():
            sink.message_added(
                mailbox
            )

    def message_removed(
        self,
        mailbox: str,
        sequence_number: int,
    ) -> None:
        for sink in self._snapshot():
            sink.message_removed(
                mailbox,
                sequence_number,
            )

    def flags_changed(
        self,
        mailbox: str,
    ) -> None:
        for sink in self._snapshot():
            sink.flags_changed(
                mailbox
            )