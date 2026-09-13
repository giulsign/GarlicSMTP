# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0

# See LICENSE for the full license terms.


from pathlib import Path

import pytest

from garlicsmtp.first_run import verify_tor_first_run
from garlicsmtp.first_run import (
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


def test_run_first_run_provisions_imap_then_verifies_tor(
    tmp_path,
    monkeypatch,
):
    from garlicsmtp.first_run import run_first_run

    paths = ApplicationPaths(
        root_dir=tmp_path,
    )
    calls = []

    def provision(*, paths, password):
        calls.append(
            ("imap", paths, password)
        )

    def verify(*, onion_service):
        calls.append(
            ("tor", onion_service)
        )

    onion_service = object()

    monkeypatch.setattr(
        "garlicsmtp.first_run.provision_imap_credentials",
        provision,
    )
    monkeypatch.setattr(
        "garlicsmtp.first_run.verify_tor_first_run",
        verify,
    )

    run_first_run(
        paths=paths,
        password="secret-password",
        onion_service=onion_service,
    )

    assert calls == [
        (
            "imap",
            paths,
            "secret-password",
        ),
        (
            "tor",
            onion_service,
        ),
    ]


def test_run_first_run_stops_before_tor_when_imap_provisioning_fails(
    tmp_path,
    monkeypatch,
):
    from garlicsmtp.first_run import run_first_run

    paths = ApplicationPaths(
        root_dir=tmp_path,
    )
    tor_calls = []

    def provision(*, paths, password):
        raise FileExistsError(
            paths.imap_credentials_file
        )

    def verify(*, onion_service):
        tor_calls.append(onion_service)

    monkeypatch.setattr(
        "garlicsmtp.first_run.provision_imap_credentials",
        provision,
    )
    monkeypatch.setattr(
        "garlicsmtp.first_run.verify_tor_first_run",
        verify,
    )

    with pytest.raises(FileExistsError):
        run_first_run(
            paths=paths,
            password="secret-password",
            onion_service=object(),
        )

    assert tor_calls == []


def test_run_first_run_propagates_tor_verification_failure(
    tmp_path,
    monkeypatch,
):
    from garlicsmtp.first_run import run_first_run

    paths = ApplicationPaths(
        root_dir=tmp_path,
    )

    def provision(*, paths, password):
        return None

    def verify(*, onion_service):
        raise RuntimeError(
            "Tor first-run verification failed"
        )

    monkeypatch.setattr(
        "garlicsmtp.first_run.provision_imap_credentials",
        provision,
    )
    monkeypatch.setattr(
        "garlicsmtp.first_run.verify_tor_first_run",
        verify,
    )

    with pytest.raises(
        RuntimeError,
        match="Tor first-run verification failed",
    ):
        run_first_run(
            paths=paths,
            password="secret-password",
            onion_service=object(),
        )


def test_run_first_run_reuses_existing_imap_credentials(
    tmp_path,
    monkeypatch,
):
    from garlicsmtp.first_run import run_first_run

    paths = ApplicationPaths(
        root_dir=tmp_path,
    )
    paths.imap_credentials_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    paths.imap_credentials_file.write_text(
        "existing-credentials",
        encoding="utf-8",
    )

    calls = []

    def provision(*, paths, password):
        calls.append("imap")

    def verify(*, onion_service):
        calls.append("tor")

    monkeypatch.setattr(
        "garlicsmtp.first_run.provision_imap_credentials",
        provision,
    )
    monkeypatch.setattr(
        "garlicsmtp.first_run.verify_tor_first_run",
        verify,
    )

    run_first_run(
        paths=paths,
        password="new-password",
        onion_service=object(),
    )

    assert calls == ["tor"]


def test_run_first_run_reuses_existing_imap_credentials_without_password(
    tmp_path,
    monkeypatch,
):
    from garlicsmtp.first_run import run_first_run

    paths = ApplicationPaths(
        root_dir=tmp_path,
    )
    paths.imap_credentials_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    paths.imap_credentials_file.write_text(
        "existing-credentials",
        encoding="utf-8",
    )

    tor_calls = []

    monkeypatch.setattr(
        "garlicsmtp.first_run.verify_tor_first_run",
        lambda *, onion_service: tor_calls.append(onion_service),
    )

    onion_service = object()

    run_first_run(
        paths=paths,
        password=None,
        onion_service=onion_service,
    )

    assert tor_calls == [onion_service]


def test_run_first_run_requires_password_when_imap_credentials_are_missing(
    tmp_path,
):
    from garlicsmtp.first_run import run_first_run

    paths = ApplicationPaths(
        root_dir=tmp_path,
    )

    with pytest.raises(
        ValueError,
        match="IMAP password",
    ):
        run_first_run(
            paths=paths,
            password=None,
            onion_service=object(),
        )