from garlicsmtp.tor.control.exceptions import (
    TorControlProtocolError,
)
from garlicsmtp.tor.control.reply import (
    TorReply,
)
from garlicsmtp.tor.control.safecookie import (
    SafeCookieChallenge,
    SafeCookieEngine,
)


class SafeCookieChallengeParser:

    def __init__(
        self,
        *,
        engine: SafeCookieEngine | None = None,
    ) -> None:
        self.engine = (
            engine
            or SafeCookieEngine()
        )

    def parse(
        self,
        reply: TorReply,
        *,
        client_nonce: bytes,
    ) -> SafeCookieChallenge:
        self._validate_client_nonce(
            client_nonce
        )

        if not reply.successful:
            raise TorControlProtocolError(
                "AUTHCHALLENGE command failed "
                f"with status {reply.status}"
            )

        challenge_line = self._find_challenge_line(
            reply
        )

        arguments = self._parse_arguments(
            challenge_line.text
        )

        server_hash_text = arguments.get(
            "SERVERHASH"
        )

        if server_hash_text is None:
            raise TorControlProtocolError(
                "AUTHCHALLENGE reply does not "
                "contain SERVERHASH"
            )

        server_nonce_text = arguments.get(
            "SERVERNONCE"
        )

        if server_nonce_text is None:
            raise TorControlProtocolError(
                "AUTHCHALLENGE reply does not "
                "contain SERVERNONCE"
            )

        server_hash = self.engine.decode_hex(
            server_hash_text,
            name="SERVERHASH",
        )

        server_nonce = self.engine.decode_hex(
            server_nonce_text,
            name="SERVERNONCE",
        )

        return SafeCookieChallenge(
            client_nonce=client_nonce,
            server_nonce=server_nonce,
            server_hash=server_hash,
        )

    @staticmethod
    def _find_challenge_line(
        reply: TorReply,
    ):
        matches = reply.find_all(
            "AUTHCHALLENGE"
        )

        if not matches:
            raise TorControlProtocolError(
                "AUTHCHALLENGE reply does not "
                "contain an AUTHCHALLENGE line"
            )

        if len(matches) != 1:
            raise TorControlProtocolError(
                "AUTHCHALLENGE reply contains "
                "multiple challenge lines"
            )

        return matches[0]

    @staticmethod
    def _parse_arguments(
        text: str,
    ) -> dict[str, str]:
        keyword, separator, remainder = (
            text.partition(
                " "
            )
        )

        if keyword.upper() != "AUTHCHALLENGE":
            raise TorControlProtocolError(
                "Unexpected AUTHCHALLENGE "
                "reply keyword"
            )

        if not separator:
            raise TorControlProtocolError(
                "AUTHCHALLENGE reply does not "
                "contain challenge arguments"
            )

        arguments: dict[str, str] = {}

        for token in remainder.split():
            key, separator, value = (
                token.partition(
                    "="
                )
            )

            if not separator:
                continue

            if not key:
                raise TorControlProtocolError(
                    "Malformed AUTHCHALLENGE "
                    "argument"
                )

            normalized = key.upper()

            if normalized in arguments:
                raise TorControlProtocolError(
                    "Duplicate AUTHCHALLENGE "
                    f"argument {normalized}"
                )

            arguments[
                normalized
            ] = value

        return arguments

    def _validate_client_nonce(
        self,
        client_nonce: bytes,
    ) -> None:
        # Riutilizziamo la validazione stretta
        # già implementata dal motore.
        self.engine.encode_hex(
            client_nonce
        )
