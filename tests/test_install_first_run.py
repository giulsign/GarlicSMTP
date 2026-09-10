# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0

# See LICENSE for the full license terms.


from pathlib import Path

import pytest

from install.first_run import verify_tor_first_run
from install.first_run import (
    provision_imap_credentials,
)
from garlicsmtp.configuration.paths import (
    ApplicationPaths,
)
from garlicsmtp.security.auth.persistent_imap_authenticator import (
    PersistentImapAuthenticator,
)


class FakeOnionServiceManager:
    def __init__(
        self,
        identity_file: Path,
    ):
        self.calls = 0
        self.hostname = "a" * 56 + ".onion"
        self.identity_file = identity_file

    def start(self):
        self.calls += 1


def test_tor_first_run_starts_onion_service_manager(
    tmp_path,
):
    identity_file = (
        tmp_path
        / "onion-service.key"
    )
    identity_file.write_text(
        "ED25519-V3:test-private-key",
        encoding="utf-8",
    )

    onion_service = FakeOnionServiceManager(
        identity_file
    )

    verify_tor_first_run(
        onion_service=onion_service,
    )

    assert onion_service.calls == 1


def test_tor_first_run_rejects_missing_onion_hostname(
    tmp_path,
):
    identity_file = (
        tmp_path
        / "onion-service.key"
    )
    identity_file.write_text(
        "ED25519-V3:test-private-key",
        encoding="utf-8",
    )

    onion_service = FakeOnionServiceManager(
        identity_file
    )
    onion_service.hostname = None

    with pytest.raises(
        RuntimeError,
        match="hostname",
    ):
        verify_tor_first_run(
            onion_service=onion_service,
        )


def test_tor_first_run_rejects_invalid_onion_hostname(
    tmp_path,
):
    identity_file = (
        tmp_path
        / "onion-service.key"
    )
    identity_file.write_text(
        "ED25519-V3:test-private-key",
        encoding="utf-8",
    )

    onion_service = FakeOnionServiceManager(
        identity_file
    )
    onion_service.hostname = "not-an-onion-hostname"

    with pytest.raises(
        RuntimeError,
        match="hostname",
    ):
        verify_tor_first_run(
            onion_service=onion_service,
        )


def test_tor_first_run_rejects_missing_onion_identity(
    tmp_path,
):
    onion_service = FakeOnionServiceManager(
        tmp_path
        / "onion-service.key"
    )

    with pytest.raises(
        RuntimeError,
        match="identity",
    ):
        verify_tor_first_run(
            onion_service=onion_service,
        )


def test_first_run_provisions_imap_credentials(
    tmp_path,
):
    paths = ApplicationPaths(
        root_dir=tmp_path,
    )

    provision_imap_credentials(
        paths=paths,
        password="secret-password",
    )

    assert paths.imap_credentials_file.exists()

    authenticator = PersistentImapAuthenticator(
        path=paths.imap_credentials_file,
    )

    assert authenticator.authenticate(
        "garlicsmtp",
        "secret-password",
    ) is True


def test_first_run_does_not_regenerate_existing_imap_credentials(
    tmp_path,
):
    paths = ApplicationPaths(
        root_dir=tmp_path,
    )

    provision_imap_credentials(
        paths=paths,
        password="first-password",
    )

    original = paths.imap_credentials_file.read_bytes()

    with pytest.raises(
        FileExistsError,
    ):
        provision_imap_credentials(
            paths=paths,
            password="second-password",
        )

    assert (
        paths.imap_credentials_file.read_bytes()
        == original
    )
