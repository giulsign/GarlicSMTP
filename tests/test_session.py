# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.smtp.session import SMTPSession
from garlicsmtp.smtp.state import SMTPState


def test_session_initial_state():
    session = SMTPSession("127.0.0.1")
    assert session.client_ip == "127.0.0.1"
    assert session.state == SMTPState.CONNECT