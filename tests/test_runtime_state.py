# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.core.engine import RuntimeState


def test_runtime_state_values():

    assert RuntimeState.STOPPED.name == "STOPPED"
    assert RuntimeState.STARTING.name == "STARTING"
    assert RuntimeState.RUNNING.name == "RUNNING"
    assert RuntimeState.STOPPING.name == "STOPPING"