# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from abc import ABC, abstractmethod


class Tickable(ABC):

    @abstractmethod
    def tick(self) -> None:
        raise NotImplementedError