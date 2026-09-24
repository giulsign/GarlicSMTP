# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.smtp.dispatcher import CommandDispatcher

from garlicsmtp.smtp.handlers.ehlo import EHLOHandler

from garlicsmtp.smtp.parser import SMTPParser

from garlicsmtp.smtp.session import SMTPSession


dispatcher = CommandDispatcher()

dispatcher.register(
    "EHLO",
    EHLOHandler()
)

session = SMTPSession(
    "127.0.0.1"
)

cmd = SMTPParser.parse(
    "EHLO garlic.onion"
)

reply = dispatcher.dispatch(
    session,
    cmd
)


