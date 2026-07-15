"""
SMTP DATA receiver.
"""


class SMTPDataReceiver:

    def __init__(self):

        self.lines = []

    def append(self, line: str):

        #
        # RFC5321 Dot-Stuffing
        #

        if line.startswith(".."):

            line = line[1:]

        self.lines.append(line)

    def finished(self, line: str):

        return line == "."

    def body(self):

        return "\n".join(self.lines)
