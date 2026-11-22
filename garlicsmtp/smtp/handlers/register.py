# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from typing import TYPE_CHECKING

from garlicsmtp.smtp.dispatcher import CommandDispatcher
from garlicsmtp.smtp.handlers.ehlo import EHLOHandler
from garlicsmtp.smtp.handlers.mail import MailHandler
from garlicsmtp.smtp.handlers.rcpt import RCPTHandler
from garlicsmtp.smtp.handlers.data import DataHandler

if TYPE_CHECKING:
    from garlicsmtp.application.address_policy import AddressPolicy


def create_dispatcher(e2ee_capability: str | None = None, address_policy: "AddressPolicy | None" = None,):

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

        RCPTHandler(address_policy=address_policy)

    )

    dispatcher.register(

        "DATA",

        DataHandler()

    )

    return dispatcher
