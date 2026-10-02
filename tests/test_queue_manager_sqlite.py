# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from datetime import UTC, datetime, timedelta

from garlicsmtp.queue.factory import QueueFactory
from garlicsmtp.queue.manager import QueueManager
from garlicsmtp.queue.sqlite import SQLiteQueueBackend


def test_queue_manager_can_use_sqlite_backend(tmp_path, message):

    backend = SQLiteQueueBackend(
        tmp_path / "queue.db"
    )

    queue = QueueManager(
        backend=backend,
    )

    item = QueueFactory.create(message)

    queue.enqueue(item)

    assert queue.size() == 1
    assert queue.peek().id == item.id

    queue.ack(item)

    assert queue.empty()


def test_queue_manager_can_retry_pending_sqlite_items(
    tmp_path,
    message,
):
    backend = SQLiteQueueBackend(
        tmp_path / "queue.db"
    )

    queue = QueueManager(
        backend=backend,
    )

    item = QueueFactory.create(message)
    item.attempts = 8
    item.last_error = "TemporaryDeliveryError"
    item.next_retry = (
        datetime.now(UTC)
        + timedelta(hours=2)
    )

    queue.enqueue(item)

    assert queue.peek() is None

    retried = queue.retry_pending()

    assert retried == 1

    ready = queue.peek()

    assert ready is not None
    assert ready.id == item.id
    assert ready.next_retry is None
    assert ready.attempts == 8
    assert (
        ready.last_error
        == "TemporaryDeliveryError"
    )