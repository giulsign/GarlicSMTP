# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from abc import ABC, abstractmethod

from garlicsmtp.models.message import MailMessage
from garlicsmtp.storage.entry import VerificationStatus


class MessageVerifier(ABC):

    @abstractmethod
    def verify(
        self,
        message: MailMessage,
    ) -> VerificationStatus:
        """
        Verify the authenticity and integrity of a message.

        The verification result is local trust metadata and
        must not modify the message being verified.
        """
        raise NotImplementedError
