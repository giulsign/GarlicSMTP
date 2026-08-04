from garlicsmtp.application.status import (
    ApplicationStatus,
)
from garlicsmtp.application.tor_status import (
    TorStatus,
)
from garlicsmtp.core.engine.state import (
    RuntimeState,
)


def make_tor_status(
    *,
    enabled: bool = True,
    socks_available: bool = False,
    control_enabled: bool = False,
    control_available: bool = False,
    authenticated: bool = False,
    authentication_method: str = "DISABLED",
    version: str | None = None,
    bootstrap_progress: int | None = None,
    bootstrap_summary: str | None = None,
    built_circuits: int = 0,
    active_streams: int = 0,
    last_error: str | None = (
        "Tor control is disabled"
    ),
    socks_listeners: tuple[str, ...] = (),
    control_listeners: tuple[str, ...] = (),
) -> TorStatus:
    return TorStatus(
        enabled=enabled,
        socks_host="127.0.0.1",
        socks_port=9050,
        socks_available=socks_available,
        control_enabled=control_enabled,
        control_host="127.0.0.1",
        control_port=9051,
        control_available=control_available,
        authenticated=authenticated,
        authentication_method=(
            authentication_method
        ),
        version=version,
        bootstrap_progress=(
            bootstrap_progress
        ),
        bootstrap_summary=(
            bootstrap_summary
        ),
        built_circuits=built_circuits,
        active_streams=active_streams,
        new_circuits_allowed=False,
        new_circuits_available=False,
        last_error=last_error,
        socks_listeners=socks_listeners,
        control_listeners=(
            control_listeners
        ),
        onion_smtp_port=25,
    )


def make_application_status(
    *,
    runtime_state: RuntimeState = (
        RuntimeState.STOPPED
    ),
    smtp_running: bool = False,
    imap_running: bool = False,
    queue_worker_running: bool = False,
    smtp_connections: int = 0,
    imap_connections: int = 0,
    pending_messages: int = 0,
    mailboxes: tuple[str, ...] = (),
    tor: TorStatus | None = None,
    smtp_host: str = "127.0.0.1",
    smtp_port: int = 2525,
    imap_host: str = "127.0.0.1",
    imap_port: int = 1143,
) -> ApplicationStatus:
    return ApplicationStatus(
        runtime_state=runtime_state,
        smtp_running=smtp_running,
        imap_running=imap_running,
        queue_worker_running=(
            queue_worker_running
        ),
        smtp_connections=(
            smtp_connections
        ),
        imap_connections=(
            imap_connections
        ),
        pending_messages=(
            pending_messages
        ),
        mailboxes=tuple(
            mailboxes
        ),
        hostname="garlicsmtp.local",
        local_domain="test.onion",
        tor=(
            tor
            if tor is not None
            else make_tor_status()
        ),
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        imap_host=imap_host,
        imap_port=imap_port,
    )
