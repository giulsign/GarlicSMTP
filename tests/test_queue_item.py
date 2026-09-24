# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.queue.item import QueueItem
from garlicsmtp.queue.factory import QueueFactory
from datetime import UTC, datetime, timedelta


def test_queue_item_creation(message):

    item = QueueItem.create(

        "ABC123",

        message

    )

    assert item.id == "ABC123"

    assert item.attempts == 0

    assert item.message is message


def test_queue_item_retry_defaults(message):

    item = QueueFactory.create(message)

    assert item.attempts == 0
    assert item.next_retry is None
    assert item.last_error is None


def test_queue_item_is_ready_by_default(message):

    item = QueueFactory.create(message)

    assert item.ready() is True


def test_queue_item_is_not_ready_before_retry(message):

    item = QueueFactory.create(message)

    item.next_retry = datetime.now(UTC) + timedelta(minutes=5)

    assert item.ready() is False


def test_queue_item_is_ready_after_retry_time(message):

    item = QueueFactory.create(message)

    item.next_retry = datetime.now(UTC) - timedelta(minutes=5)

    assert item.ready() is True
