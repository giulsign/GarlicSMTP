# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.application.context import (
    ApplicationContext,
)
from garlicsmtp.application.status import (
    ApplicationStatus,
)
from garlicsmtp.application.mailbox_summary import (
    MailboxSummary,
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
        mailboxes = tuple(
            self.context.store.list_mailboxes()
        )

        mailbox_summaries = tuple(
            MailboxSummary(
                address=mailbox,
                message_count=len(
                    self.context.store.list_messages(
                        mailbox
                    )
                ),
            )
            for mailbox in mailboxes
        )

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
            smtp_host=(
                self.context.settings.smtp.host
            ),
            smtp_port=(
                self.context.settings.smtp.port
            ),
            imap_host=(
                self.context.settings.imap.host
            ),
            imap_port=(
                self.context.settings.imap.port
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
            mailboxes=mailboxes,
            hostname=(
                self.context.settings.hostname
            ),
            local_domain=(
                self.context.settings.local_domain
            ),
            tor=self.context.tor_monitor.status,
            mailbox_summaries=(
                mailbox_summaries
            ),
        )
