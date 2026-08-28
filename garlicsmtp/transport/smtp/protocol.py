# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.transport.smtp.connection import SMTPConnection
from garlicsmtp.transport.smtp.reply import SMTPServerReply
from garlicsmtp.transport.smtp.exceptions import SMTPClientError


class SMTPClientProtocol:

    def __init__(self, connection: SMTPConnection):
        self.connection = connection

    def read_reply(self) -> SMTPServerReply:
        first_line = self.connection.receive_line()

        if first_line is None:
            raise SMTPClientError(
                "SMTP server closed the connection"
            )

        reply = self.parse_reply(first_line)

        if len(first_line) < 4 or first_line[3] != "-":
            return reply

        messages = [reply.message]
        expected_code = str(reply.code)

        while True:
            line = self.connection.receive_line()

            if line is None:
                raise SMTPClientError(
                    "SMTP server closed a multiline reply"
                )

            if len(line) < 4:
                raise SMTPClientError(
                    f"Invalid SMTP reply: {line!r}"
                )

            code = line[:3]
            separator = line[3]
            message = line[4:].strip()

            if code != expected_code:
                raise SMTPClientError(
                    f"Unexpected SMTP reply code: {code}"
                )

            messages.append(message)

            if separator == " ":
                break

            if separator != "-":
                raise SMTPClientError(
                    f"Invalid SMTP reply separator: {separator!r}"
                )

        return SMTPServerReply(
            reply.code,
            "\n".join(messages),
        )

    def send_command(self, command: str):
        self.connection.send(
            command + "\r\n"
        )

    @staticmethod
    def parse_reply(text: str) -> SMTPServerReply:
        code = int(text[:3])
        message = text[4:].strip()

        return SMTPServerReply(
            code,
            message,
        )
    
    def greeting(self) -> SMTPServerReply:
        reply = self.read_reply()

        if reply.code != 220:
            raise SMTPClientError(
                f"SMTP greeting failed ({reply.code})"
            )

        return reply

    def ehlo(
        self,
        hostname: str,
    ) -> SMTPServerReply:

        return self._execute(
            f"EHLO {hostname}",
            250,
        )
        
    

    def mail_from(
        self,
        sender: str,
    ) -> SMTPServerReply:

        return self._execute(
            f"MAIL FROM:<{sender}>",
            250,
        )
    
    
    def rcpt_to(
        self,
        recipient: str,
    ) -> SMTPServerReply:

        return self._execute(
            f"RCPT TO:<{recipient}>",
            250,
        )

    
    def data(self, content: str) -> SMTPServerReply:
        self.send_command("DATA")

        reply = self.read_reply()

        if reply.code != 354:
            raise SMTPClientError(
                f"DATA failed ({reply.code})"
            )

        normalized = content.replace(
            "\r\n",
            "\n",
        ).replace(
            "\r",
            "\n",
        )

        lines = normalized.split("\n")

        stuffed = "\r\n".join(
            f".{line}" if line.startswith(".") else line
            for line in lines
        )

        self.connection.send(
            stuffed + "\r\n.\r\n"
        )

        reply = self.read_reply()

        if reply.code != 250:
            raise SMTPClientError(
                f"DATA body failed ({reply.code})"
            )

        return reply


    def quit(self) -> SMTPServerReply:
        self.send_command("QUIT")

        reply = self.read_reply()

        if reply.code != 221:
            raise SMTPClientError(
                f"QUIT failed ({reply.code})"
            )

        return reply
    
    def _execute(
        self,
        command: str,
        expected: int,
    ) -> SMTPServerReply:

        self.send_command(command)

        reply = self.read_reply()

        if reply.code != expected:
            raise SMTPClientError(
                f"{command} failed ({reply.code})"
            )

        return reply


