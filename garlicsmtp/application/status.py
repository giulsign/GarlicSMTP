from dataclasses import dataclass

from garlicsmtp.core.engine.state import (
    RuntimeState,
)
from garlicsmtp.application.tor_status import (
    TorStatus,
)


@dataclass(frozen=True, slots=True)
class ApplicationStatus:

    runtime_state: RuntimeState

    smtp_running: bool
    imap_running: bool
    queue_worker_running: bool

    smtp_host: str
    smtp_port: int

    imap_host: str
    imap_port: int

    smtp_connections: int
    imap_connections: int

    pending_messages: int

    mailboxes: tuple[str, ...]

    hostname: str
    local_domain: str

    tor: TorStatus  

    @property
    def mailbox_count(
        self,
    ) -> int:
        return len(
            self.mailboxes
        )

    @property
    def running(
        self,
    ) -> bool:
        return (
            self.runtime_state
            is RuntimeState.RUNNING
        )
