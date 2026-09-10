# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0

# See LICENSE for the full license terms.


from pathlib import Path

import pytest

from install.first_run import verify_tor_first_run


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
