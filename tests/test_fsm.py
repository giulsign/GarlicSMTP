# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.smtp.session import SMTPSession
from garlicsmtp.smtp.parser import SMTPParser
from garlicsmtp.smtp.fsm import SMTPStateMachine


session = SMTPSession("127.0.0.1")

cmd = SMTPParser.parse(
    "MAIL FROM:<a@test.onion>"
)

try:

    SMTPStateMachine.validate(
        session,
        cmd
    )

    
except Exception as e:

    print(type(e).__name__)

    print(e)
