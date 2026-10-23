# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from pathlib import Path
import tomllib

from garlicsmtp.configuration.onion_page_writer import (
    save_onion_page_settings,
)


class OnionPagePreferences:
    def __init__(self, settings_path: Path) -> None:
        self.settings_path = Path(settings_path)

    def save(
        self,
        *,
        enabled: bool,
        html_path: str,
    ) -> None:
        if enabled and not html_path.strip():
            raise ValueError(
                "HTML path is required when the custom Onion page is enabled"
            )

        save_onion_page_settings(
            self.settings_path,
            enabled=enabled,
            html_path=html_path,
        )

    def load(self) -> tuple[bool, str]:
        with self.settings_path.open("rb") as settings_file:
            configuration = tomllib.load(settings_file)

        tor = configuration.get("tor", {})

        enabled = tor.get(
            "onion_custom_page_enabled",
            False,
        )
        html_path = tor.get(
            "onion_custom_page_path",
            "",
        )

        if not isinstance(enabled, bool):
            raise ValueError(
                "onion_custom_page_enabled must be a boolean"
            )

        if not isinstance(html_path, str):
            raise ValueError(
                "onion_custom_page_path must be a string"
            )

        return enabled, html_path