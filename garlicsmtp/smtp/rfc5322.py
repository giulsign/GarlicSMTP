# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

"""
RFC5322 parser.
"""


class RFC5322Parser:

    @staticmethod

    def split(message: str):

        lines = message.splitlines()

        headers = []

        body = []

        in_body = False

        for line in lines:

            if not in_body:

                if line == "":

                    in_body = True

                    continue

                headers.append(line)

            else:

                body.append(line)

        return headers, body
