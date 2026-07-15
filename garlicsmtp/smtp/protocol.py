from garlicsmtp.core.pipeline import LoggerStage, Pipeline, PipelineContext
from garlicsmtp.smtp.connection import SMTPConnection
from garlicsmtp.smtp.engine import SMTPEngine
from garlicsmtp.smtp.handlers.register import create_dispatcher
from garlicsmtp.smtp.parser import SMTPParser
from garlicsmtp.smtp.replies import ReplyFactory
from garlicsmtp.smtp.session import SMTPSession
from garlicsmtp.smtp.state import SMTPState
from garlicsmtp.queue.manager import QueueManager
from garlicsmtp.queue.stage import QueueStage


class SMTPProtocol:
    """
    Gestisce il dialogo SMTP di una singola connessione.
    """

    def __init__(
                self,
                connection: SMTPConnection,
                hostname: str = "localhost",
                pipeline: Pipeline | None = None,
            ):
                self.connection = connection
                self.hostname = hostname
                self.session = SMTPSession(connection.ip)
                self.dispatcher = create_dispatcher()
                self.engine = SMTPEngine()

                if pipeline is None:
                    self.queue = QueueManager()

                    self.pipeline = Pipeline()
                    self.pipeline.add(LoggerStage())
                    self.pipeline.add(QueueStage(self.queue))
                else:
                    self.queue = None
                    self.pipeline = pipeline

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
                context = PipelineContext(
                    message=self.session.message,
                )

                context = self.pipeline.execute(context)

                if context.accepted:
                    reply = ReplyFactory.ok("Message accepted")
                else:
                    reply = ReplyFactory.transaction_failed(
                        context.reject_reason
                    )

                self.connection.send(reply.serialize())

            return True

        command = SMTPParser.parse(line)

        if command.command == "QUIT":
            reply = ReplyFactory.bye()
            self.connection.send(reply.serialize())
            return False

        reply = self.dispatcher.dispatch(
            self.session,
            command,
        )

        self.connection.send(reply.serialize())

        return True

    def serve(self) -> None:
        self.send_greeting()

        while self.process_one_command():
            pass

        self.close()

    def close(self) -> None:
        self.connection.close()