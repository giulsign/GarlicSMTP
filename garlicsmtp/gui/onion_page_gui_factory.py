# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from pathlib import Path

from garlicsmtp.gui.onion_page_preferences import (
    OnionPagePreferences,
)


def create_onion_page_preferences(
    settings_path: Path | str,
) -> OnionPagePreferences:
    return OnionPagePreferences(
        Path(settings_path),
    )
