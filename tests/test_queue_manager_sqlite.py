# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

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