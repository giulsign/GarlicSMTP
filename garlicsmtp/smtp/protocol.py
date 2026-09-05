# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from cryptography.exceptions import InvalidTag

from garlicsmtp.core.pipeline import Pipeline, PipelineContext
from garlicsmtp.security.encryptor import (
    ENCRYPTION_HEADER,
)
from garlicsmtp.security.verifier import MessageVerifier
from garlicsmtp.smtp.connection import SMTPConnection
from garlicsmtp.smtp.engine import SMTPEngine
from garlicsmtp.smtp.handlers.register import create_dispatcher
from garlicsmtp.smtp.parser import SMTPParser
from garlicsmtp.smtp.replies import ReplyFactory
from garlicsmtp.smtp.session import SMTPSession
from garlicsmtp.smtp.state import SMTPState
from garlicsmtp.storage.entry import (
    VerificationStatus,
)


class SMTPProtocol:
    """
    Gestisce il dialogo SMTP di una singola connessione.
    """

    def __init__(
        self,
        connection: SMTPConnection,
        hostname: str = "localhost",
        pipeline: Pipeline | None = None,
        verifier: MessageVerifier | None = None,
        e2ee_capability: str | None = None,
        decryptor=None,
        encryption_private_key=None,
    ):
        if pipeline is None:
            raise ValueError(
                "SMTPProtocol requires a delivery pipeline"
            )

        self.connection = connection
        self.hostname = hostname
        self.session = SMTPSession(
            connection.ip
        )
        self.dispatcher = create_dispatcher(e2ee_capability=e2ee_capability)
        self.engine = SMTPEngine()
        self.pipeline = pipeline
        self.verifier = verifier
        self.decryptor = decryptor
        self.encryption_private_key = (
            encryption_private_key
        )

    def send_greeting(self) -> None:
        reply = ReplyFactory.greeting(self.hostname)
        self.connection.send(reply.serialize())

    def receive_command(self) -> str | None:
        return self.connection.receive_line()

    def process_one_command(self) -> bool:
        line = self.receive_command()

        if line is None:
            return False

        if self.session.state == SMTPState.RECEIVE_DATA:
            done = self.engine.receive_data(
                self.session,
                line,
            )

            if done:
                if self.session.data_error:
                    reply = ReplyFactory.transaction_failed()

                    self.connection.send(
                        reply.serialize()
                    )

                    return True

                message = self.session.message

                if (
                    message.headers.get(
                        ENCRYPTION_HEADER
                    )
                    is not None
                ):
                    if self.decryptor is None:
                        reply = (
                            ReplyFactory
                            .transaction_failed()
                        )

                        self.connection.send(
                            reply.serialize()
                        )

                        return True

                    if self.encryption_private_key is None:
                        reply = (
                            ReplyFactory
                            .transaction_failed()
                        )

                        self.connection.send(
                            reply.serialize()
                        )

                        return True

                    try:
                        message = self.decryptor.decrypt(
                            message,
                            self.encryption_private_key,
                        )
                    except (
                        ValueError,
                        InvalidTag,
                    ):
                        reply = (
                            ReplyFactory
                            .transaction_failed()
                        )

                        self.connection.send(
                            reply.serialize()
                        )

                        return True

                verification_status = (
                    self.verifier.verify(
                        message
                    )
                    if self.verifier is not None
                    else VerificationStatus.UNSIGNED
                )

                context = PipelineContext(
                    message=message,
                    verification_status=verification_status,
                )

                context = self.pipeline.execute(
                    context
                )

                if context.accepted:
                    reply = ReplyFactory.ok(
                        "Message accepted"
                    )
                else:
                    reply = ReplyFactory.transaction_failed()

                self.connection.send(
                    reply.serialize()
                )

            # Una riga appartenente a DATA non deve
            # mai cadere nel parser dei comandi SMTP.
            return True

        command = SMTPParser.parse(line)

        if command.command == "QUIT":
            reply = ReplyFactory.bye()

            self.connection.send(
                reply.serialize()
            )

            return False

        reply = self.dispatcher.dispatch(
            self.session,
            command,
        )

        self.connection.send(
            reply.serialize()
        )

        return True

    def serve(self) -> None:
        self.send_greeting()

        while self.process_one_command():
            pass

        self.close()

    def close(self) -> None:
        self.connection.close()