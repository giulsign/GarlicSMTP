# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.exceptions import (
    DeliveryError,
    GarlicSMTPError,
    PermanentDeliveryError,
    TemporaryDeliveryError,
)


def test_delivery_exception_hierarchy():

    assert issubclass(DeliveryError, GarlicSMTPError)
    assert issubclass(TemporaryDeliveryError, DeliveryError)
    assert issubclass(PermanentDeliveryError, DeliveryError)