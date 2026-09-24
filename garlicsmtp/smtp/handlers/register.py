# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.smtp.dispatcher import CommandDispatcher
from garlicsmtp.smtp.handlers.ehlo import EHLOHandler
from garlicsmtp.smtp.handlers.mail import MailHandler
from garlicsmtp.smtp.handlers.rcpt import RCPTHandler
from garlicsmtp.smtp.handlers.data import DataHandler


def create_dispatcher(e2ee_capability: str | None = None,):

    dispatcher = CommandDispatcher()

    dispatcher.register(

        "EHLO",

        EHLOHandler(e2ee_capability=e2ee_capability)

    )

    dispatcher.register(

        "MAIL",

        MailHandler()

    )

    dispatcher.register(

        "RCPT",

        RCPTHandler()

    )

    dispatcher.register(

        "DATA",

        DataHandler()

    )

    return dispatcher
