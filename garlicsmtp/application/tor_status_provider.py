import shlex
from collections.abc import Callable

from garlicsmtp.application.tor_status import (
    TorStatus,
)
from garlicsmtp.configuration import (
    TorSettings,
)
from garlicsmtp.tor.control import (
    SafeCookieAuthenticator,
    TorControlClient,
    TorControlConnection,
)


TorControlClientFactory = Callable[
    [],
    TorControlClient,
]


class TorStatusProvider:

    INFO_KEYS = (
        "version",
        "status/bootstrap-phase",
        "net/listeners/socks",
        "net/listeners/control",
        "circuit-status",
        "stream-status",
    )

    def __init__(
        self,
        settings: TorSettings,
        *,
        client_factory=None,
        authenticator_factory=None,
        onion_hostname_provider=None,
    ) -> None:
        self.settings = settings

        self.client_factory = (
            client_factory
            or self._build_client
        )

        self.authenticator_factory = (
            authenticator_factory
            or self._build_authenticator
        )

        self.onion_hostname_provider = (
            onion_hostname_provider
        )

    def snapshot(
        self,
    ) -> TorStatus:
        if not self.settings.enabled:
            return self.initial_status()

        if not self.settings.control_enabled:
            return self.initial_status()

        if not self.settings.require_safecookie:
            return self.initial_status()

        client = self.client_factory()  

        try:
            client.connect()

            authenticator = (
                self.authenticator_factory(
                    client
                )
            )

            protocol_info = (
                authenticator.authenticate()
            )

            values = client.get_info(
                *self.INFO_KEYS
            )

            (
                bootstrap_progress,
                bootstrap_summary,
            ) = self._parse_bootstrap(
                values.get(
                    "status/bootstrap-phase"
                )
            )

            socks_listeners = (
                self._parse_listeners(
                    values.get(
                        "net/listeners/socks"
                    )
                )
            )

            control_listeners = (
                self._parse_listeners(
                    values.get(
                        "net/listeners/control"
                    )
                )
            )

            built_circuits = (
                self._count_built_circuits(
                    values.get(
                        "circuit-status"
                    )
                )
            )

            active_streams = (
                self._count_active_streams(
                    values.get(
                        "stream-status"
                    )
                )
            )

            return TorStatus(
                enabled=True,
                socks_host=(
                    self.settings.socks_host
                ),
                socks_port=(
                    self.settings.socks_port
                ),
                socks_available=bool(
                    socks_listeners
                ),
                control_enabled=True,
                control_host=(
                    self.settings.control_host
                ),
                control_port=(
                    self.settings.control_port
                ),
                control_available=True,
                authenticated=True,
                authentication_method=(
                    "SAFECOOKIE"
                ),
                version=(
                    values.get("version")
                    or protocol_info.tor_version
                ),
                bootstrap_progress=(
                    bootstrap_progress
                ),
                bootstrap_summary=(
                    bootstrap_summary
                ),
                built_circuits=(
                    built_circuits
                ),
                active_streams=(
                    active_streams
                ),
                new_circuits_allowed=(
                    self.settings
                    .allow_new_circuits
                ),
                new_circuits_available=(
                    self.settings
                    .allow_new_circuits
                    and bootstrap_progress == 100
                ),
                last_error=None,
                socks_listeners=(
                    socks_listeners
                ),
                control_listeners=(
                    control_listeners
                ),
                onion_smtp_port=(
                    self.settings
                    .onion_smtp_port
                ),
                onion_hostname=(
                    self._onion_hostname()
                ),
            )

        except Exception as exc:
            return self._unavailable(
                error=self._safe_error(exc)
            )

        finally:
            client.close()

    def _build_client(
        self,
    ) -> TorControlClient:
        connection = TorControlConnection(
            host=(
                self.settings.control_host
            ),
            port=(
                self.settings.control_port
            ),
        )

        return TorControlClient(
            connection=connection
        )

    def _unavailable(
        self,
        *,
        error: str,
    ) -> TorStatus:
        return TorStatus(
            enabled=self.settings.enabled,
            socks_host=(
                self.settings.socks_host
            ),
            socks_port=(
                self.settings.socks_port
            ),
            socks_available=False,
            control_enabled=(
                self.settings.control_enabled
            ),
            control_host=(
                self.settings.control_host
            ),
            control_port=(
                self.settings.control_port
            ),
            control_available=False,
            authenticated=False,
            authentication_method=(
                "SAFECOOKIE"
                if (
                    self.settings
                    .control_enabled
                    and self.settings
                    .require_safecookie
                )
                else "DISABLED"
            ),
            version=None,
            bootstrap_progress=None,
            bootstrap_summary=None,
            built_circuits=0,
            active_streams=0,
            new_circuits_allowed=(
                self.settings
                .allow_new_circuits
            ),
            new_circuits_available=False,
            last_error=error,
            socks_listeners=(),
            control_listeners=(),
            onion_smtp_port=(
                self.settings
                .onion_smtp_port
            ),
            onion_hostname=(
                self._onion_hostname()
            ),
        )

    @staticmethod
    def _parse_bootstrap(
        value: str | None,
    ) -> tuple[
        int | None,
        str | None,
    ]:
        if not value:
            return (
                None,
                None,
            )

        try:
            tokens = shlex.split(
                value
            )
        except ValueError:
            return (
                None,
                None,
            )

        arguments: dict[str, str] = {}

        for token in tokens:
            key, separator, item = (
                token.partition("=")
            )

            if separator:
                arguments[
                    key.upper()
                ] = item

        progress_text = arguments.get(
            "PROGRESS"
        )

        progress = None

        if (
            progress_text is not None
            and progress_text.isdigit()
        ):
            numeric_progress = int(
                progress_text
            )

            if 0 <= numeric_progress <= 100:
                progress = numeric_progress

        summary = arguments.get(
            "SUMMARY"
        )

        return (
            progress,
            summary,
        )

    @staticmethod
    def _parse_listeners(
        value: str | None,
    ) -> tuple[str, ...]:
        if not value:
            return ()

        try:
            return tuple(
                shlex.split(value)
            )
        except ValueError:
            return ()

    @staticmethod
    def _count_built_circuits(
        value: str | None,
    ) -> int:
        if not value:
            return 0

        return sum(
            1
            for line in value.splitlines()
            if (
                len(line.split()) >= 2
                and line.split()[1]
                == "BUILT"
            )
        )

    @staticmethod
    def _count_active_streams(
        value: str | None,
    ) -> int:
        if not value:
            return 0

        terminal_states = {
            "CLOSED",
            "FAILED",
            "DETACHED",
        }

        return sum(
            1
            for line in value.splitlines()
            if (
                len(line.split()) >= 2
                and line.split()[1]
                not in terminal_states
            )
        )

    @staticmethod
    def _safe_error(
        exc: Exception,
    ) -> str:
        # Non riportiamo path del cookie,
        # nonce, hash o dettagli crittografici.
        return (
            "Tor control status unavailable: "
            f"{type(exc).__name__}"
        )

    def _build_authenticator(
        self,
        client,
    ):
        return SafeCookieAuthenticator(
            client=client,
            configured_cookie_file=(
                self.settings.cookie_file
            ),
        )

    def _onion_hostname(
        self,
    ) -> str | None:
        if self.onion_hostname_provider is None:
            return None

        return self.onion_hostname_provider()

    def initial_status(
        self,
    ) -> TorStatus:
        onion_hostname=(
            self._onion_hostname()
        ),
        if not self.settings.enabled:
            error = "Tor transport is disabled"

        elif not self.settings.control_enabled:
            error = "Tor control is disabled"

        elif not self.settings.require_safecookie:
            error = (
                "Tor control requires "
                "SAFECOOKIE authentication"
            )

        else:
            error = "Tor status not checked yet"

        return self._unavailable(
            error=error
        )

