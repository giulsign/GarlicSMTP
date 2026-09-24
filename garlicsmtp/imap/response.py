# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from abc import ABC, abstractmethod

from garlicsmtp.network.text import TextConnection


class IMAPResponse(ABC):

    @abstractmethod
    def send(
        self,
        connection: TextConnection,
    ) -> None:
        raise NotImplementedError