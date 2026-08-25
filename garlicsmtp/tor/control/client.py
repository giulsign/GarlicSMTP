from collections.abc import Callable

from garlicsmtp.tor.control.auth_challenge import (
    SafeCookieChallengeParser,
)
from garlicsmtp.tor.control.connection import (
    TorControlConnection,
)
from garlicsmtp.tor.control.exceptions import (
    TorControlProtocolError,
    TorControlSecurityError,
)
from garlicsmtp.tor.control.parser import (
    TorReplyParser,
)
from garlicsmtp.tor.control.protocol_info import (
    ProtocolInfo,
    ProtocolInfoParser,
)
from garlicsmtp.tor.control.reply import (
    TorReply,
)
from garlicsmtp.tor.control.safecookie import (
    SafeCookieChallenge,
    SafeCookieEngine,
)
from dataclasses import dataclass


EventListener = Callable[
    [TorReply],
    None,
]

@dataclass(
    frozen=True,
    slots=True,
)
class OnionService:
    service_id: str
    private_key: str

class TorControlClient:

    def __init__(
        self,
        *,
        connection: (
            TorControlConnection | None
        ) = None,
        reply_parser: (
            TorReplyParser | None
        ) = None,
        protocol_info_parser: (
            ProtocolInfoParser | None
        ) = None,
        challenge_parser: (
            SafeCookieChallengeParser | None
        ) = None,
        safecookie_engine: (
            SafeCookieEngine | None
        ) = None,
    ) -> None:
        self.connection = (
            connection
            or TorControlConnection()
        )

        self.reply_parser = (
            reply_parser
            or TorReplyParser()
        )

        self.protocol_info_parser = (
            protocol_info_parser
            or ProtocolInfoParser()
        )

        self.safecookie_engine = (
            safecookie_engine
            or SafeCookieEngine()
        )

        self.challenge_parser = (
            challenge_parser
            or SafeCookieChallengeParser(
                engine=self.safecookie_engine
            )
        )

        self._protocol_info_requested = False
        self._auth_challenge_requested = False
        self._authenticated = False

        self._event_listeners: list[
            EventListener
        ] = []

    @property
    def connected(
        self,
    ) -> bool:
        return self.connection.connected

    @property
    def authenticated(
        self,
    ) -> bool:
        return self._authenticated

    def connect(
        self,
    ) -> None:
        if self.connected:
            return

        self.connection.connect()

        self._protocol_info_requested = False
        self._auth_challenge_requested = False
        self._authenticated = False

    def close(
        self,
    ) -> None:
        self.connection.close()

        self._protocol_info_requested = False
        self._auth_challenge_requested = False
        self._authenticated = False

    def subscribe_events(
        self,
        listener: EventListener,
    ) -> None:
        if listener not in self._event_listeners:
            self._event_listeners.append(
                listener
            )

    def unsubscribe_events(
        self,
        listener: EventListener,
    ) -> None:
        if listener in self._event_listeners:
            self._event_listeners.remove(
                listener
            )

    def protocol_info(
        self,
    ) -> ProtocolInfo:
        if self._protocol_info_requested:
            raise TorControlProtocolError(
                "PROTOCOLINFO may only be "
                "requested once per connection"
            )

        self._require_connected()

        self._protocol_info_requested = True

        reply = self._execute_command(
            "PROTOCOLINFO 1"
        )

        return self.protocol_info_parser.parse(
            reply
        )

    def auth_challenge(
        self,
        client_nonce: bytes,
    ) -> SafeCookieChallenge:
        self._require_connected()

        if self._authenticated:
            raise TorControlProtocolError(
                "Tor Control client is "
                "already authenticated"
            )

        if self._auth_challenge_requested:
            raise TorControlProtocolError(
                "AUTHCHALLENGE may only be "
                "requested once per connection"
            )

        encoded_nonce = (
            self.safecookie_engine
            .encode_hex(
                client_nonce
            )
        )

        self._auth_challenge_requested = True

        reply = self._execute_command(
            (
                "AUTHCHALLENGE SAFECOOKIE "
                f"{encoded_nonce}"
            )
        )

        return self.challenge_parser.parse(
            reply,
            client_nonce=client_nonce,
        )

    def authenticate_safecookie_hash(
        self,
        client_hash: bytes,
    ) -> None:
        self._require_connected()

        if not self._auth_challenge_requested:
            raise TorControlProtocolError(
                "AUTHENTICATE requires a "
                "successful AUTHCHALLENGE"
            )

        if self._authenticated:
            raise TorControlProtocolError(
                "Tor Control client is "
                "already authenticated"
            )

        encoded_hash = (
            self.safecookie_engine
            .encode_hex(
                client_hash
            )
        )

        try:
            reply = self._execute_command(
                f"AUTHENTICATE {encoded_hash}"
            )

            if not reply.successful:
                raise TorControlSecurityError(
                    "Tor SAFECOOKIE "
                    "authentication failed"
                )

            self._authenticated = True

        except Exception:
            self.close()
            raise

    def _execute_command(
        self,
        command: str,
    ) -> TorReply:
        self._require_connected()

        self.connection.send_line(
            command
        )

        return self._receive_command_reply()

    def _receive_command_reply(
        self,
    ) -> TorReply:
        while True:
            reply = self.reply_parser.parse(
                self.connection.receive_line
            )

            if reply.asynchronous:
                self._publish_event(
                    reply
                )
                continue

            return reply

    def _publish_event(
        self,
        reply: TorReply,
    ) -> None:
        for listener in tuple(
            self._event_listeners
        ):
            listener(
                reply
            )

    def _require_connected(
        self,
    ) -> None:
        if not self.connected:
            raise TorControlProtocolError(
                "Tor Control client "
                "is not connected"
            )

    def __enter__(
        self,
    ) -> "TorControlClient":
        self.connect()
        return self

    def __exit__(
        self,
        exc_type,
        exc,
        traceback,
    ) -> None:
        self.close()

    def get_info(
        self,
        *keys: str,
    ) -> dict[str, str]:
        self._require_authenticated()

        if not keys:
            raise TorControlProtocolError(
                "GETINFO requires at least one key"
            )

        normalized_keys = tuple(
            self._validate_info_key(key)
            for key in keys
        )

        reply = self._execute_command(
            "GETINFO "
            + " ".join(normalized_keys)
        )

        if not reply.successful:
            raise TorControlProtocolError(
                "Tor GETINFO command failed "
                f"with status {reply.status}"
            )

        values: dict[str, str] = {}

        for line in reply.lines:
            if line.is_final:
                continue

            keyword = line.keyword

            if keyword is None:
                continue

            if line.has_data:
                value = line.data_text
            else:
                value = line.value

            values[keyword] = value

        return values

    def add_onion(
        self,
        *,
        key: str,
        virtual_port: int,
        target_host: str,
        target_port: int,
    ) -> OnionService:
        self._require_authenticated()

        reply = self._execute_command(
            (
                f"ADD_ONION {key} "
                f"Port={virtual_port},"
                f"{target_host}:{target_port}"
            )
        )

        if not reply.successful:
            raise TorControlProtocolError(
                "Tor ADD_ONION command failed "
                f"with status {reply.status}"
            )

        service_line = reply.find(
            "ServiceID"
        )

        private_key_line = reply.find(
            "PrivateKey"
        )

        if service_line is None:
            raise TorControlProtocolError(
                "Tor ADD_ONION response "
                "missing ServiceID"
            )

        service_id = (
            service_line.value.strip()
        )

        if not service_id:
            raise TorControlProtocolError(
                "Tor ADD_ONION returned "
                "an empty ServiceID"
            )

        if key.startswith("NEW:"):
            if private_key_line is None:
                raise TorControlProtocolError(
                    "Tor ADD_ONION response "
                    "missing PrivateKey"
                )

            private_key = (
                private_key_line.value.strip()
            )

            if not private_key:
                raise TorControlProtocolError(
                    "Tor ADD_ONION returned "
                    "an empty PrivateKey"
                )

        else:
            private_key = key

        return OnionService(
            service_id=service_id,
            private_key=private_key,
        )
    

    def _require_authenticated(
        self,
    ) -> None:
        self._require_connected()

        if not self._authenticated:
            raise TorControlSecurityError(
                "Tor Control client "
                "is not authenticated"
            )


    @staticmethod
    def _validate_info_key(
        key: str,
    ) -> str:
        if not isinstance(key, str):
            raise TypeError(
                "GETINFO key must be text"
            )

        if not key:
            raise TorControlProtocolError(
                "GETINFO key cannot be empty"
            )

        if any(
            character.isspace()
            or character in "\r\n"
            for character in key
        ):
            raise TorControlProtocolError(
                "GETINFO key contains "
                "invalid characters"
            )

        return key