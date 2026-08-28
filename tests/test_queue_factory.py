# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.queue.factory import QueueFactory


def test_queue_factory(message):

    item = QueueFactory.create(message)

    assert item.message is message

    assert item.attempts == 0

    assert item.next_retry is None

    assert item.id

    assert item.created is not None