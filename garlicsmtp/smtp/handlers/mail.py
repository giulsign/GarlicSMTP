from garlicsmtp.smtp.handlers.base import SMTPHandler

from garlicsmtp.smtp.replies import ReplyFactory

from garlicsmtp.smtp.state import SMTPState


class MailHandler(SMTPHandler):

    def handle(self, session, command):

        session.message.envelope.sender = command.arguments["from"]

        session.state = SMTPState.WAIT_RCPT

        return ReplyFactory.ok(
            "Sender OK"
        )
