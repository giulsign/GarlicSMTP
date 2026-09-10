# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0

# See LICENSE for the full license terms.


import re
from garlicsmtp.configuration.paths import (
    ApplicationPaths,
)
from garlicsmtp.security.auth.imap_credentials import (
    ImapCredentialStore,
)


_ONION_V3_HOSTNAME = re.compile(
    r"^[a-z2-7]{56}\.onion$"
)


def verify_tor_first_run(
    onion_service,
) -> None:
    onion_service.start()

    hostname = onion_service.hostname

    if (
        hostname is None
        or _ONION_V3_HOSTNAME.fullmatch(hostname) is None
    ):
        raise RuntimeError(
            "Tor first-run did not produce a valid Onion hostname"
        )

    if not onion_service.identity_file.exists():
        raise RuntimeError(
            "Tor first-run did not persist the Onion identity"
        )


def provision_imap_credentials(
    *,
    paths: ApplicationPaths,
    password: str,
) -> None:
    ImapCredentialStore(
        path=paths.imap_credentials_file,
    ).create(
        username="garlicsmtp",
        password=password,
    )
