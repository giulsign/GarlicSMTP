from garlicsmtp.smtp.handlers.base import SMTPHandler

from garlicsmtp.smtp.state import SMTPState

from garlicsmtp.smtp.replies import ReplyFactory


class DataHandler(SMTPHandler):

    def handle(self, session, command):

        session.receiver = session.receiver.__class__()

        session.state = SMTPState.RECEIVE_DATA

        return ReplyFactory.start_data()
