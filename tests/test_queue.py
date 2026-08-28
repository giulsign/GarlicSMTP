# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.


from datetime import datetime

from garlicsmtp.queue.manager import QueueManager
from garlicsmtp.queue.item import QueueItem

from garlicsmtp.models import Envelope
from garlicsmtp.models import MailHeaders
from garlicsmtp.models import Metadata
from garlicsmtp.models import MailMessage


message = MailMessage(

    envelope=Envelope(
        sender="alice@test.onion",
        recipients=["bob@test.onion"]
    ),

    headers=MailHeaders(),

    metadata=Metadata()

)

item = QueueItem(

    id="MSG000001",

    created=datetime.now(),

    attempts=0,

    next_retry=None,

    message=message

)

queue = QueueManager()

queue.enqueue(item)

assert queue.size() == 1

retrieved = queue.dequeue()

assert retrieved.id == "MSG000001"

assert queue.size() == 0

