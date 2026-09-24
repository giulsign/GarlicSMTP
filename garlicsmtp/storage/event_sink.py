# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from abc import ABC, abstractmethod


class StoreEventSink(ABC):

    @abstractmethod
    def message_added(
        self,
        mailbox: str,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def message_removed(
        self,
        mailbox: str,
        sequence_number: int,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def flags_changed(
        self,
        mailbox: str,
    ) -> None:
        raise NotImplementedError
