"""
SMTP command parser.
"""

from garlicsmtp.models import SMTPCommand
from garlicsmtp.exceptions import SMTPProtocolError


class SMTPParser:
    """
    Parses one SMTP command line.
    """

    @staticmethod
    def parse(line: str) -> SMTPCommand:

        line = line.strip()

        if not line:
            raise SMTPProtocolError("Empty command.")

        parts = line.split(None, 1)

        command = parts[0].upper()

        argument = ""

        if len(parts) > 1:
            argument = parts[1]

        if command == "EHLO":
            return SMTPCommand(
                command="EHLO",
                arguments={
                    "domain": argument
                },
                raw=line
            )

        if command == "HELO":
            return SMTPCommand(
                command="HELO",
                arguments={
                    "domain": argument
                },
                raw=line
            )

        if command == "QUIT":
            return SMTPCommand(
                command="QUIT",
                raw=line
            )

        if command == "DATA":
            return SMTPCommand(
                command="DATA",
                raw=line
            )

        if command == "RSET":
            return SMTPCommand(
                command="RSET",
                raw=line
            )

        if command == "NOOP":
            return SMTPCommand(
                command="NOOP",
                raw=line
            )

        if command == "MAIL":

            prefix = "FROM:"

            if not argument.upper().startswith(prefix):
                raise SMTPProtocolError(
                    "MAIL command missing FROM:"
                )

            sender = argument[len(prefix):].strip()

            sender = sender.strip("<>")

            return SMTPCommand(
                command="MAIL",
                arguments={
                    "from": sender
                },
                raw=line
            )

        if command == "RCPT":

            prefix = "TO:"

            if not argument.upper().startswith(prefix):
                raise SMTPProtocolError(
                    "RCPT command missing TO:"
                )

            recipient = argument[len(prefix):].strip()

            recipient = recipient.strip("<>")

            return SMTPCommand(
                command="RCPT",
                arguments={
                    "to": recipient
                },
                raw=line
            )

        raise SMTPProtocolError(
            f"Unknown SMTP command: {command}"
        )
