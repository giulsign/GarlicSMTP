# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.smtp.headerparser import HeaderParser


def test_header_parser():
    headers = HeaderParser.parse([
        "Subject: GarlicSMTP",
        "From: alice@test.onion",
        "To: bob@test.onion",
    ])

    assert headers["Subject"] == "GarlicSMTP"
    assert headers["From"] == "alice@test.onion"
    assert headers["To"] == "bob@test.onion"