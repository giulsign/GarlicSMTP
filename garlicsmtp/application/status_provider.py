from garlicsmtp.application.context import (
    ApplicationContext,
)
from garlicsmtp.application.status import (
    ApplicationStatus,
)


class ApplicationStatusProvider:

    def __init__(
        self,
        context: ApplicationContext,
    ) -> None:
        self.context = context

    def snapshot(
        self,
    ) -> ApplicationStatus:
        return ApplicationStatus(
            runtime_state=(
                self.context.runtime.state
            ),
            smtp_running=(
                self.context.smtp_server.running
            ),
            imap_running=(
                self.context.imap_server.running
            ),
            queue_worker_running=(
                self.context.queue_worker.running
            ),
            smtp_connections=(
                self.context.smtp_server
                .active_connections
            ),
            imap_connections=(
                self.context.imap_server
                .active_connections
            ),
            pending_messages=(
                self.context.queue.size()
            ),
            mailboxes=tuple(
                self.context.store.list_mailboxes()
            ),
            hostname=(
                self.context.settings.hostname
            ),
            local_domain=(
                self.context.settings.local_domain
            ),
            tor=self.context.tor_monitor.status,
        )
