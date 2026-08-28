# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.core.service import Service


def test_service_interface():

    assert hasattr(Service, "start")
    assert hasattr(Service, "stop")