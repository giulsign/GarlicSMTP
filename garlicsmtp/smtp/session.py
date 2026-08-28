# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from dataclasses import dataclass, field

from garlicsmtp.models import Envelope, MailHeaders, MailMessage, Metadata
from garlicsmtp.smtp.datareceiver import SMTPDataReceiver
from garlicsmtp.smtp.state import SMTPState


@dataclass(slots=True)
class SMTPSession:
    client_ip: str
    helo: str = ""
    authenticated: bool = False
    state: SMTPState = SMTPState.CONNECT
    receiver: SMTPDataReceiver = field(default_factory=SMTPDataReceiver)
    message: MailMessage = field(
        default_factory=lambda: MailMessage(
            envelope=Envelope(),
            headers=MailHeaders(),
            metadata=Metadata(),
        )
    )

    def reset_transaction(self):
        self.receiver = SMTPDataReceiver()
        self.message = MailMessage(
            envelope=Envelope(),
            headers=MailHeaders(),
            metadata=Metadata(),
        )
        self.state = SMTPState.WAIT_MAIL
