# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from pathlib import Path
import tomllib

from garlicsmtp.configuration.settings import (
    ApplicationSettings,
    IMAPSettings,
    LoggingSettings,
    SMTPSettings,
    TorSettings,
)


class ConfigurationLoader:

    def load(
        self,
        path: Path,
    ) -> ApplicationSettings:
        if not path.exists():
            return ApplicationSettings()

        with path.open("rb") as file:
            data = tomllib.load(file)

        smtp_data = data.get(
            "smtp",
            {},
        )

        imap_data = data.get(
            "imap",
            {},
        )

        logging_data = data.get(
            "logging",
            {},
        )

        tor_data = data.get(
            "tor",
            {},
        )

        cookie_file_value = tor_data.get(
            "cookie_file"
        )

        cookie_file = (
            Path(cookie_file_value).expanduser()
            if cookie_file_value
            else None
        )

        return ApplicationSettings(
            hostname=data.get(
                "hostname",
                "garlicsmtp.local",
            ),
            local_domain=data.get(
                "local_domain",
                "test.onion",
            ),
            smtp=SMTPSettings(
                host=smtp_data.get(
                    "host",
                    "127.0.0.1",
                ),
                port=smtp_data.get(
                    "port",
                    2525,
                ),
            ),
            imap=IMAPSettings(
                host=imap_data.get(
                    "host",
                    "127.0.0.1",
                ),
                port=imap_data.get(
                    "port",
                    1143,
                ),
            ),
            logging=LoggingSettings(
                level=logging_data.get(
                    "level",
                    "INFO",
                ),
            ),
            tor=TorSettings(
                enabled=tor_data.get(
                    "enabled",
                    True,
                ),
                socks_host=tor_data.get(
                    "socks_host",
                    "127.0.0.1",
                ),
                socks_port=tor_data.get(
                    "socks_port",
                    9050,
                ),
                onion_smtp_port=tor_data.get(
                    "onion_smtp_port",
                    25,
                ),
                control_enabled=tor_data.get(
                    "control_enabled",
                    False,
                ),
                control_host=tor_data.get(
                    "control_host",
                    "127.0.0.1",
                ),
                control_port=tor_data.get(
                    "control_port",
                    9051,
                ),
                cookie_file=cookie_file,
                require_safecookie=tor_data.get(
                    "require_safecookie",
                    True,
                ),
                allow_new_circuits=tor_data.get(
                    "allow_new_circuits",
                    False,
                ),
            ),
        )
