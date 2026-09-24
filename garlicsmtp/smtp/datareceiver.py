# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

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
