# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.queue.factory import QueueFactory
from garlicsmtp.transport.local.transport import LocalTransport


def test_local_transport(tmp_path, message):

    transport = LocalTransport(tmp_path)

    item = QueueFactory.create(message)

    assert transport.deliver(item) is True

    files = list(tmp_path.glob("*.json"))

    assert len(files) == 1

    assert files[0].name == f"{item.id}.json"