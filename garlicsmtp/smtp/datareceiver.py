# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

"""
SMTP DATA receiver.
"""


class SMTPDataReceiver:
    MAX_MESSAGE_SIZE = 2_097_152

    def __init__(self):
        self.lines = []
        self._size = 0

    def append(self, line: str):
        #
        # RFC5321 Dot-Stuffing
        #
        if line.startswith(".."):
            line = line[1:]

        # Conteggia anche il separatore tra le righe.
        line_size = len(line.encode("utf-8"))
        if self.lines:
            line_size += 1

        if self._size + line_size > self.MAX_MESSAGE_SIZE:
            raise ValueError("SMTP message too large")

        self.lines.append(line)
        self._size += line_size

    def finished(self, line: str):
        return line == "."

    def body(self):
        return "\n".join(self.lines)
