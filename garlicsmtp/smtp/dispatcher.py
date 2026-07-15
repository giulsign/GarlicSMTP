"""
SMTP Command Dispatcher.
"""

from garlicsmtp.exceptions import SMTPProtocolError
from garlicsmtp.smtp.fsm import SMTPStateMachine


class CommandDispatcher:

    def __init__(self):
        self._handlers = {}

    def register(self, command: str, handler):
        self._handlers[command.upper()] = handler

    def dispatch(self, session, command):
        SMTPStateMachine.validate(session, command)

        handler = self._handlers.get(command.command)

        if handler is None:
            raise SMTPProtocolError(
                f"No handler for {command.command}"
            )

        return handler.handle(session, command)