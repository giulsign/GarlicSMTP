# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.models import OnionAddress


class OnionValidator:

    def resolve(
        self,
        recipient: str,
    ) -> OnionAddress:
        address = OnionAddress.parse(
            recipient
        )

        if not address.is_valid:
            raise ValueError(
                f"Invalid onion address: {recipient}"
            )

        return address

    