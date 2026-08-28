# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.smtp.parser import SMTPParser


def test_parser_commands():
    assert SMTPParser.parse("EHLO onion").command == "EHLO"
    assert SMTPParser.parse("MAIL FROM:<alice@test.onion>").arguments["from"] == "alice@test.onion"
    assert SMTPParser.parse("RCPT TO:<bob@test.onion>").arguments["to"] == "bob@test.onion"
    assert SMTPParser.parse("DATA").command == "DATA"
    assert SMTPParser.parse("QUIT").command == "QUIT"