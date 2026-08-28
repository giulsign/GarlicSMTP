# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.core.events.bus import EventBus
from garlicsmtp.core.events.handler import EventHandler
from garlicsmtp.core.events.mailaccepted import MailAcceptedEvent


class PrintHandler(EventHandler):

    def handle(self, event):

        print("Ricevuta mail")


bus = EventBus()

bus.subscribe(

    MailAcceptedEvent,

    PrintHandler()

)

from garlicsmtp.models import Envelope, MailHeaders, MailMessage, Metadata

message = MailMessage(
    envelope=Envelope(
        sender="alice@test.onion",
        recipients=["bob@test.onion"],
    ),
    headers=MailHeaders(),
    metadata=Metadata(),
)

event = MailAcceptedEvent.from_message(message)

bus.publish(event)
