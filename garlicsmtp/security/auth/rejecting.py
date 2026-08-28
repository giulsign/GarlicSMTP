# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.security.auth.authenticator import (
    Authenticator,
)


class RejectingAuthenticator(Authenticator):

    def authenticate(
        self,
        username: str,
        password: str,
    ) -> bool:
        return False