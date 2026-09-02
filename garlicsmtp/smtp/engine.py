# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import binascii
from garlicsmtp.smtp.headerparser import HeaderParser
from garlicsmtp.smtp.rfc5322 import RFC5322Parser
from garlicsmtp.smtp.state import SMTPState
from garlicsmtp.smtp.mime import MimeDecoder


class SMTPEngine:

    def receive_data(self, session, line):

        if session.receiver.finished(line):

            raw_message = session.receiver.body()

            header_lines, body_lines = RFC5322Parser.split(
                raw_message
            )

            try:
                parsed_headers = HeaderParser.parse(
                    header_lines
                )
            except ValueError:
                session.data_error = (
                    "Invalid message headers"
                )

                session.state = SMTPState.WAIT_MAIL

                return True

            for key, value in parsed_headers.items():
                session.message.headers.add(
                    key,
                    value,
                )

            raw_body = "\n".join(
                body_lines
            )

            content_type = (
                session.message.headers.get(
                    "Content-Type",
                    "",
                )
            )

            encoding = (
                session.message.headers.get(
                    "Content-Transfer-Encoding",
                    "",
                )
            )

            try:
                body = MimeDecoder.decode(
                    raw_body,
                    encoding,
                )
            except (
                binascii.Error,
                UnicodeDecodeError,
            ):
                session.data_error = (
                    "Invalid message body"
                )

                session.state = SMTPState.WAIT_MAIL

                return True

            if content_type.lower().startswith(
                "multipart/alternative"
            ):
                boundary = ""

                for parameter in content_type.split(";")[1:]:
                    name, separator, value = (
                        parameter.partition("=")
                    )

                    if (
                        separator
                        and name.strip().lower()
                        == "boundary"
                    ):
                        boundary = (
                            value.strip()
                            .strip('"')
                        )
                        break

                if boundary:
                    try:
                        body = (
                            MimeDecoder
                            .extract_multipart_alternative(
                                raw_body,
                                boundary,
                            )
                        )
                    except ValueError:
                        session.data_error = (
                            "Invalid multipart body"
                        )

                        session.state = SMTPState.WAIT_MAIL

                        return True

            session.message.body = body

            session.state = SMTPState.WAIT_MAIL

            return True

        session.receiver.append(line)

        return False