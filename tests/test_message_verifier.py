# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import pytest

from garlicsmtp.security.verifier import (
    MessageVerifier,
)


def test_message_verifier_is_abstract():
    with pytest.raises(TypeError):
        MessageVerifier()

