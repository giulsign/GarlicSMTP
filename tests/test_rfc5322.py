# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.smtp.rfc5322 import RFC5322Parser


def test_rfc5322_split():
    message = "Subject: Test\n\nHello\nWorld\n"

    headers, body = RFC5322Parser.split(message)

    assert headers == ["Subject: Test"]
    assert body == ["Hello", "World"]