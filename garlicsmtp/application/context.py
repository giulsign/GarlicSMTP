# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from garlicsmtp.configuration import (
    ApplicationPaths,
    ApplicationSettings,
)
from garlicsmtp.core.pipeline import Pipeline
from garlicsmtp.imap.server import IMAPServer
from garlicsmtp.logger import Logger
from garlicsmtp.queue.manager import QueueManager
from garlicsmtp.queue.worker import QueueWorker
from garlicsmtp.smtp.server import SMTPServer
from garlicsmtp.storage.store import MessageStore
from garlicsmtp.transport.manager import (
    TransportManager,
)

if TYPE_CHECKING:
    from garlicsmtp.core.engine.runtime import (
        Runtime,
    )

from garlicsmtp.application.tor_monitor_service import (
    TorMonitorService,
)
from garlicsmtp.application.event_hub import (
    ApplicationEventHub,
)
from garlicsmtp.application.event_log import (
    ApplicationEventLog,
)
from garlicsmtp.application.event_service import (
    ApplicationEventService,
)
from garlicsmtp.tor.onion_service_manager import (
    OnionServiceManager,
)


@dataclass(slots=True)
class ApplicationContext:

    paths: ApplicationPaths
    settings: ApplicationSettings

    logger: Logger
    event_hub: ApplicationEventHub

    event_log: ApplicationEventLog
    event_service: ApplicationEventService

    store: MessageStore
    queue: QueueManager
    transport: TransportManager
    pipeline: Pipeline

    smtp_server: SMTPServer
    imap_server: IMAPServer
    queue_worker: QueueWorker

    runtime: Runtime
    onion_service: OnionServiceManager | None
    tor_monitor: TorMonitorService