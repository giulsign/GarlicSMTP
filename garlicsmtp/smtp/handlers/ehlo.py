from garlicsmtp.smtp.handlers.base import SMTPHandler
from garlicsmtp.smtp.replies import ReplyFactory
from garlicsmtp.smtp.state import SMTPState


class EHLOHandler(SMTPHandler):
    def handle(self, session, command):
        session.helo = command.arguments["domain"]
        session.state = SMTPState.WAIT_MAIL

        return ReplyFactory.ok(
            f"Hello {session.helo}"
        )
