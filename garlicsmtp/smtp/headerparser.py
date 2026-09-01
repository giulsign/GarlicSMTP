# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.security.signature_header import (
    SIGNATURE_HEADER,
)

class HeaderParser:
    @staticmethod
    def parse(lines):
        headers = {}
        current = None

        signature_name = SIGNATURE_HEADER.lower()
        signature_seen = False

        for line in lines:
            #
            # Header continuato (RFC5322 Folding)
            #
            if line.startswith((" ", "\t")):
                if current is not None:
                    headers[current] += (
                        " " + line.strip()
                    )

                continue

            if ":" not in line:
                continue

            key, value = line.split(":", 1)

            key = key.strip()
            value = value.strip()

            if key.lower() == signature_name:
                if signature_seen:
                    raise ValueError(
                        "Duplicate signature header"
                    )

                signature_seen = True

            headers[key] = value
            current = key

        return headers