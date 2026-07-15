from garlicsmtp.smtp.dispatcher import CommandDispatcher

from garlicsmtp.smtp.handlers.ehlo import EHLOHandler

from garlicsmtp.smtp.handlers.mail import MailHandler

from garlicsmtp.smtp.handlers.rcpt import RCPTHandler

from garlicsmtp.smtp.handlers.data import DataHandler


def create_dispatcher():

    dispatcher = CommandDispatcher()

    dispatcher.register(

        "EHLO",

        EHLOHandler()

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
