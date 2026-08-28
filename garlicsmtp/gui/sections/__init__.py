# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.gui.sections.application_section import (
    ApplicationSection,
)
from garlicsmtp.gui.sections.services_section import (
    ServicesSection,
)
from garlicsmtp.gui.sections.tor_section import (
    TorSection,
)
from garlicsmtp.gui.sections.activity_section import (
    ActivitySection,
)
from garlicsmtp.gui.sections.mail_metrics_section import (
    MailMetricsSection,
)
from garlicsmtp.gui.sections.mailbox_list_section import (
    MailboxListSection,
)
from garlicsmtp.gui.sections.message_list_section import (
    MessageListSection,
)
from garlicsmtp.gui.sections.message_preview_section import (
    MessagePreviewSection,
)
from .compose_section import ComposeSection

__all__ = [
    "ApplicationSection",
    "ServicesSection",
    "TorSection",
    "ActivitySection",
    "MailMetricsSection",
    "MailboxListSection",
    "MessageListSection",
    "MessagePreviewSection",
    "ComposeSection"
]
