from dataclasses import dataclass

from garlicsmtp.application.controller import (
    ApplicationController,
)
from garlicsmtp.application.status import (
    ApplicationStatus,
)
from garlicsmtp.core.engine.state import (
    RuntimeState,
)
from garlicsmtp.application.activity import (
    ApplicationActivityFormatter,
)
from garlicsmtp.application.mailbox_view_model import (
    MailboxItemViewModel,
)
from garlicsmtp.application.message_list_view_model import (
    MessageListViewModel,
)
from garlicsmtp.application.message_preview_view_model import (
    MessagePreviewViewModel,
)

class EmptyMessagePreviewExplorer:

    def get_message(
        self,
        mailbox: str,
        message_id: str,
    ):
        del mailbox
        del message_id
        return None

@dataclass(frozen=True, slots=True)
class ServiceViewModel:

    name: str
    running: bool
    status_text: str
    status_key: str

    @classmethod
    def create(
        cls,
        *,
        name: str,
        running: bool,
    ) -> "ServiceViewModel":
        return cls(
            name=name,
            running=running,
            status_text=(
                "Running"
                if running
                else "Stopped"
            ),
            status_key=(
                "running"
                if running
                else "stopped"
            ),
        )

class EmptyMessageExplorer:

    def list_messages(
        self,
        mailbox: str,
    ):
        del mailbox
        return ()

class ApplicationViewModel:

    def __init__(
        self,
        controller,
        message_list: MessageListViewModel | None = None,
        message_preview: MessagePreviewViewModel | None = None,
    ) -> None:
        self.message_preview = (
            message_preview
            if message_preview is not None
            else MessagePreviewViewModel(
                EmptyMessagePreviewExplorer()
            )
        )
        self.controller = controller
        self._status = (
            self.controller.status()
        )
        self.message_list = (
            message_list
            if message_list is not None
            else MessageListViewModel(
                EmptyMessageExplorer()
            )
        )
        self._listeners = []
        self.activity_formatter = (
            ApplicationActivityFormatter()
        )

        subscribe = getattr(
            self.controller,
            "subscribe",
            None,
        )

        if subscribe is not None:
            subscribe(
                self._handle_application_event
            )

    @property
    def status(
        self,
    ) -> ApplicationStatus:
        return self._status 

    def refresh(
        self,
    ) -> ApplicationStatus:
        self._status = (
            self.controller.status()
        )

        if self.message_preview.message_id is not None:
            self.message_preview.refresh()

        if (
            self.message_list
            .selected_mailbox
            is not None
        ):
            self.message_list.refresh()

        return self._status

    def start(
        self,
    ) -> ApplicationStatus:
        self._status = (
            self.controller.start()
        )

        return self._status

    def stop(
        self,
    ) -> ApplicationStatus:
        self._status = (
            self.controller.stop()
        )

        return self._status

    def restart(
        self,
    ) -> ApplicationStatus:
        self._status = (
            self.controller.restart()
        )

        return self._status

    @property
    def application_name(
        self,
    ) -> str:
        return "GarlicSMTP"

    @property
    def hostname(
        self,
    ) -> str:
        return self._status.hostname

    @property
    def local_domain(
        self,
    ) -> str:
        return self._status.local_domain

    @property
    def runtime_text(
        self,
    ) -> str:
        labels = {
            RuntimeState.STOPPED: "Stopped",
            RuntimeState.STARTING: "Starting",
            RuntimeState.RUNNING: "Running",
            RuntimeState.STOPPING: "Stopping",
        }

        return labels[
            self._status.runtime_state
        ]

    @property
    def runtime_status_key(
        self,
    ) -> str:
        keys = {
            RuntimeState.STOPPED: "stopped",
            RuntimeState.STARTING: "starting",
            RuntimeState.RUNNING: "running",
            RuntimeState.STOPPING: "stopping",
        }

        return keys[
            self._status.runtime_state
        ]

    @property
    def is_running(
        self,
    ) -> bool:
        return self._status.running

    @property
    def can_start(
        self,
    ) -> bool:
        return (
            self._status.runtime_state
            is RuntimeState.STOPPED
        )

    @property
    def can_stop(
        self,
    ) -> bool:
        return (
            self._status.runtime_state
            is RuntimeState.RUNNING
        )

    @property
    def can_restart(
        self,
    ) -> bool:
        return (
            self._status.runtime_state
            is RuntimeState.RUNNING
        )

    @property
    def smtp(
        self,
    ) -> ServiceViewModel:
        return ServiceViewModel.create(
            name="SMTP Server",
            running=(
                self._status.smtp_running
            ),
        )

    @property
    def imap(
        self,
    ) -> ServiceViewModel:
        return ServiceViewModel.create(
            name="IMAP Server",
            running=(
                self._status.imap_running
            ),
        )

    @property
    def queue_worker(
        self,
    ) -> ServiceViewModel:
        return ServiceViewModel.create(
            name="Queue Worker",
            running=(
                self._status
                .queue_worker_running
            ),
        )

    @property
    def smtp_connections_text(
        self,
    ) -> str:
        return self._format_count(
            self._status.smtp_connections,
            singular="connection",
            plural="connections",
        )

    @property
    def imap_connections_text(
        self,
    ) -> str:
        return self._format_count(
            self._status.imap_connections,
            singular="connection",
            plural="connections",
        )

    @property
    def pending_messages_text(
        self,
    ) -> str:
        return self._format_count(
            self._status.pending_messages,
            singular="message queued",
            plural="messages queued",
        )

    @property
    def mailbox_count_text(
        self,
    ) -> str:
        return self._format_count(
            self._status.mailbox_count,
            singular="mailbox",
            plural="mailboxes",
        )

    @property
    def mailbox_names(
        self,
    ) -> tuple[str, ...]:
        return self._status.mailboxes

    @property
    def mailbox_names_text(
        self,
    ) -> str:
        if not self._status.mailboxes:
            return "No mailboxes"

        return ", ".join(
            self._status.mailboxes
        )

    @staticmethod
    def _format_count(
        value: int,
        *,
        singular: str,
        plural: str,
    ) -> str:
        label = (
            singular
            if value == 1
            else plural
        )

        return f"{value} {label}"


    @property
    def tor_enabled(
        self,
    ) -> bool:
        return self._status.tor.enabled


    @property
    def tor_ready(
        self,
    ) -> bool:
        return self._status.tor.ready


    @property
    def tor_status_text(
        self,
    ) -> str:
        tor = self._status.tor

        if not tor.enabled:
            return "Disabled"

        if tor.ready:
            return "Ready"

        if tor.authenticated:
            return "Authenticated"

        return "Unavailable"


    @property
    def tor_status_key(
        self,
    ) -> str:
        if not self._status.tor.enabled:
            return "disabled"

        if self._status.tor.ready:
            return "running"

        return "stopped"


    @property
    def tor_socks_endpoint_text(
        self,
    ) -> str:
        return (
            self._status.tor
            .socks_listeners_text
        )


    @property
    def tor_control_endpoint_text(
        self,
    ) -> str:
        tor = self._status.tor

        if not tor.control_enabled:
            return "Disabled"

        return tor.control_listeners_text


    @property
    def tor_version_text(
        self,
    ) -> str:
        return (
            self._status.tor.version
            or "Unknown"
        )


    @property
    def tor_bootstrap_text(
        self,
    ) -> str:
        tor = self._status.tor

        if tor.bootstrap_progress is None:
            return "Unknown"

        summary = (
            f" — {tor.bootstrap_summary}"
            if tor.bootstrap_summary
            else ""
        )

        return (
            f"{tor.bootstrap_progress}%"
            f"{summary}"
        )


    @property
    def tor_circuits_text(
        self,
    ) -> str:
        value = (
            self._status.tor
            .built_circuits
        )

        label = (
            "circuit"
            if value == 1
            else "circuits"
        )

        return f"{value} built {label}"


    @property
    def tor_streams_text(
        self,
    ) -> str:
        value = (
            self._status.tor
            .active_streams
        )

        label = (
            "stream"
            if value == 1
            else "streams"
        )

        return f"{value} active {label}"


    @property
    def tor_onion_smtp_port_text(
        self,
    ) -> str:
        return str(
            self._status.tor
            .onion_smtp_port
        )


    @property
    def tor_error_text(
        self,
    ) -> str:
        return (
            self._status.tor.last_error
            or "None"
        )

    def subscribe(
        self,
        listener,
    ) -> None:
        if listener not in self._listeners:
            self._listeners.append(
                listener
            )


    def unsubscribe(
        self,
        listener,
    ) -> None:
        if listener in self._listeners:
            self._listeners.remove(
                listener
            )


    def close(
        self,
    ) -> None:
        unsubscribe = getattr(
            self.controller,
            "unsubscribe",
            None,
        )

        if unsubscribe is not None:
            unsubscribe(
                self._handle_application_event
            )

        self._listeners.clear()


    def _handle_application_event(
        self,
    ) -> None:
        self._status = (
            self.controller.status()
        )

        if self.message_preview.message_id is not None:
            self.message_preview.refresh()

        if (
            self.message_list
            .selected_mailbox
            is not None
        ):
            self.message_list.refresh()

        for listener in tuple(
            self._listeners
        ):
            listener()

    @property
    def smtp_endpoint_text(
        self,
    ) -> str:
        return (
            f"{self._status.smtp_host}:"
            f"{self._status.smtp_port}"
        )


    @property
    def imap_endpoint_text(
        self,
    ) -> str:
        return (
            f"{self._status.imap_host}:"
            f"{self._status.imap_port}"
        )

    @property
    def events(
        self,
    ):
        context = getattr(
            self.controller,
            "context",
            None,
        )

        if context is None:
            return ()

        event_log = getattr(
            context,
            "event_log",
            None,
        )

        if event_log is None:
            return ()

        return event_log.snapshot(
            newest_first=True
        )

    @property
    def activity_entries(
        self,
    ):
        return (
            self.activity_formatter
            .format_many(
                self.events
            )
        )

    @property
    def tor_authentication_text(    
        self,
    ) -> str:
        return (
            self._status.tor
            .authentication_method
        )

    def clear_activity(
        self,
    ) -> None:
        context = getattr(
            self.controller,
            "context",
            None,
        )

        if context is None:
            return

        event_log = getattr(
            context,
            "event_log",
            None,
        )

        if event_log is None:
            return

        event_log.clear()

        for listener in tuple(
            self._listeners
        ):
            listener()

    @property
    def activity_count(
        self,
    ) -> int:
        return len(
            self.activity_entries
        )

    @property
    def mailbox_items(
        self,
    ) -> tuple[
        MailboxItemViewModel,
        ...
    ]:
        summaries = (
            self._status.mailbox_summaries
        )

        if not summaries:
            return tuple(
                MailboxItemViewModel(
                    address=address,
                    message_count=0,
                )
                for address in self._status.mailboxes
            )

        return tuple(
            MailboxItemViewModel.from_summary(
                summary
            )
            for summary in summaries
        )


    @property
    def stored_message_count(
        self,
    ) -> int:
        return (
            self._status
            .total_stored_messages
        )


    @property
    def stored_message_count_text(
        self,
    ) -> str:
        count = self.stored_message_count

        if count == 1:
            return "1 stored message"

        return f"{count} stored messages"