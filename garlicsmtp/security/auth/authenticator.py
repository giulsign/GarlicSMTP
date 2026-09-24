# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from abc import ABC, abstractmethod


class Authenticator(ABC):

    @abstractmethod
    def authenticate(
        self,
        username: str,
        password: str,
    ) -> bool:
        raise NotImplementedError