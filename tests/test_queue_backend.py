# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import queue

from garlicsmtp.queue.backend import QueueBackend
from garlicsmtp.queue.manager import QueueManager
from datetime import UTC, datetime, timedelta

from garlicsmtp.queue.factory import (
    QueueFactory,
)
from garlicsmtp.queue.memory import (
    MemoryQueueBackend,
)


class SpyBackend(QueueBackend):

    def __init__(self):
        self.calls = []

    def enqueue(self, item):
        self.calls.append(("enqueue", item))

    def dequeue(self):
        self.calls.append(("dequeue",))
        return None

    def peek(self):
        self.calls.append(("peek",))
        return None

    def ack(self, item):
        self.calls.append(("ack", item))
        return True

    def nack(self, item):
        self.calls.append(("nack", item))
        return True

    def size(self):
        self.calls.append(("size",))
        return 0

    def empty(self):
        self.calls.append(("empty",))
        return True
    
    def update(self, item):
        self.calls.append(("update", item))
        return True

    def retry_pending(self):
        self.calls.append(
            ("retry_pending",)
        )
        return 0


def test_queue_manager_delegates_to_backend():

    backend = SpyBackend()

    queue = QueueManager(
        backend=backend,
    )

    marker = object()

    queue.enqueue(marker)
    queue.peek()
    queue.ack(marker)
    queue.nack(marker)
    queue.size()
    queue.empty()
    queue.update(marker)
    queue.retry_pending()

    assert backend.calls == [
        ("enqueue", marker),
        ("peek",),
        ("ack", marker),
        ("nack", marker),
        ("size",),
        ("empty",),
        ("update", marker),
        ("retry_pending",)
    ]


def test_memory_queue_peek_skips_not_ready_item(
    message,
):
    backend = MemoryQueueBackend()

    first = QueueFactory.create(
        message
    )

    first.next_retry = (
        datetime.now(UTC)
        + timedelta(hours=1)
    )

    second = QueueFactory.create(
        message
    )

    second.next_retry = None

    backend.enqueue(first)
    backend.enqueue(second)

    item = backend.peek()

    assert item is second


def test_memory_queue_ack_removes_ready_item_not_at_head(
    message,
):
    backend = MemoryQueueBackend()

    first = QueueFactory.create(
        message
    )

    first.next_retry = (
        datetime.now(UTC)
        + timedelta(hours=1)
    )

    second = QueueFactory.create(
        message
    )

    backend.enqueue(first)
    backend.enqueue(second)

    assert backend.peek() is second
    assert backend.ack(second) is True
    assert backend.size() == 1


def test_memory_queue_retry_pending_makes_suspended_items_ready(
    message,
):
    backend = MemoryQueueBackend()

    suspended = QueueFactory.create(
        message
    )
    suspended.attempts = 8
    suspended.last_error = "TemporaryDeliveryError"
    suspended.next_retry = (
        datetime.now(UTC)
        + timedelta(hours=2)
    )

    ready = QueueFactory.create(
        message
    )
    ready.attempts = 1
    ready.last_error = None
    ready.next_retry = None

    backend.enqueue(suspended)
    backend.enqueue(ready)

    retried = backend.retry_pending()

    assert retried == 1

    item = backend.peek()

    assert item is suspended
    assert item.next_retry is None
    assert item.attempts == 8
    assert (
        item.last_error
        == "TemporaryDeliveryError"
    )