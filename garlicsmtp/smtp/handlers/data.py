# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.smtp.handlers.base import SMTPHandler

from garlicsmtp.smtp.state import SMTPState

from garlicsmtp.smtp.replies import ReplyFactory


class DataHandler(SMTPHandler):

    def handle(self, session, command):

        session.receiver = session.receiver.__class__()

        session.state = SMTPState.RECEIVE_DATA

        return ReplyFactory.start_data()
