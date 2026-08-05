from dataclasses import dataclass

from garlicsmtp.core.engine.state import (
    RuntimeState,
)
from garlicsmtp.application.tor_status import (
    TorStatus,
)
from garlicsmtp.application.mailbox_summary import (
    MailboxSummary,
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
    mailbox_summaries: tuple[
        MailboxSummary,
        ...
    ] = ()

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

    @property
    def total_stored_messages(
        self,
    ) -> int:
        return sum(
            mailbox.message_count
            for mailbox in self.mailbox_summaries
        )
