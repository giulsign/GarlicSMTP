# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from pathlib import Path
import tomllib

from garlicsmtp.configuration import onion_page_writer

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

        if enabled:
            html_file = Path(html_path).expanduser()

            if not html_file.is_absolute():
                html_file = self.settings_path.absolute().parent / html_file

            if html_file.is_dir():
                raise ValueError(
                    "HTML file path must point to a file, not a directory"
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

    
    def load_website(self) -> tuple[bool, str]:
        with self.settings_path.open("rb") as settings_file:
            configuration = tomllib.load(settings_file)

        tor = configuration.get("tor", {})

        enabled = tor.get(
            "onion_website_enabled",
            False,
        )
        html_path = tor.get(
            "onion_website_index_path",
            "",
        )

        if not isinstance(enabled, bool):
            raise ValueError(
                "onion_website_enabled must be a boolean"
            )

        if not isinstance(html_path, str):
            raise ValueError(
                "onion_website_index_path must be a string"
            )

        return enabled, html_path

    
    def save_website(
        self,
        *,
        enabled: bool,
        html_path: str,
    ) -> None:
        if enabled and not html_path.strip():
            raise ValueError(
                "HTML path is required when the Onion website is enabled"
            )

        if enabled:
            html_file = Path(html_path).expanduser()

            if not html_file.is_absolute():
                html_file = (
                    self.settings_path.absolute().parent / html_file
                )

            if html_file.is_dir():
                raise ValueError(
                    "HTML file path must point to a file, not a directory"
                )

        onion_page_writer.save_onion_website_settings(
            self.settings_path,
            enabled=enabled,
            html_path=html_path,
        )

    
    def save_combined(
        self,
        *,
        custom_enabled: bool,
        custom_html_path: str,
        website_enabled: bool,
        website_index_path: str,
    ) -> None:
        
        if custom_enabled and not custom_html_path.strip():
            raise ValueError(
                "HTML path is required when the custom Onion page is enabled"
            )
        
        if custom_enabled:
            html_file = Path(custom_html_path).expanduser()

            if not html_file.is_absolute():
                html_file = (
                    self.settings_path.absolute().parent / html_file
                )

            if html_file.is_dir():
                raise ValueError(
                    "HTML file path must point to a file, not a directory"
                )
        
        if website_enabled and not website_index_path.strip():
            raise ValueError(
                "HTML path is required when the Onion website is enabled"
            )
        
        if website_enabled:
            html_file = Path(website_index_path).expanduser()

            if not html_file.is_absolute():
                html_file = (
                    self.settings_path.absolute().parent / html_file
                )

            if html_file.is_dir():
                raise ValueError(
                    "HTML file path must point to a file, not a directory"
                )

        onion_page_writer.save_onion_combined_settings(
            self.settings_path,
            custom_enabled=custom_enabled,
            custom_html_path=custom_html_path,
            website_enabled=website_enabled,
            website_index_path=website_index_path,
        )