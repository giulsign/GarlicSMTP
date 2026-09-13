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


def run_first_run(
    *,
    paths: ApplicationPaths,
    password: str | None,
    onion_service,
) -> None:
    if not paths.imap_credentials_file.exists():
        if password is None:
            raise ValueError(
                "IMAP password is required for first-run"
            )

        provision_imap_credentials(
            paths=paths,
            password=password,
        )

    verify_tor_first_run(
        onion_service=onion_service,
    )
