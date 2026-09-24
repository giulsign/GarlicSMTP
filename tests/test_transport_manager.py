# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.queue.factory import QueueFactory
from garlicsmtp.transport.dummy import DummyTransport
from garlicsmtp.transport.manager import TransportManager


def test_transport_manager_delivers(message):

    item = QueueFactory.create(message)

    dummy = DummyTransport()
    manager = TransportManager(dummy)

    result = manager.deliver(item)

    assert result is True
    assert dummy.delivered == [item]