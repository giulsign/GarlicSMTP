from garlicsmtp.smtp.headerparser import HeaderParser
from garlicsmtp.smtp.rfc5322 import RFC5322Parser
from garlicsmtp.smtp.state import SMTPState


class SMTPEngine:

    def receive_data(self, session, line):

        if session.receiver.finished(line):

            raw_message = session.receiver.body()

            header_lines, body_lines = RFC5322Parser.split(
                raw_message
            )

            parsed_headers = HeaderParser.parse(
                header_lines
            )

            for key, value in parsed_headers.items():
                session.message.headers.add(
                    key,
                    value,
                )

            session.message.body = "\n".join(body_lines)

            session.state = SMTPState.WAIT_MAIL

            return True

        session.receiver.append(line)

        return False