# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import os
import stat

import pytest

from garlicsmtp.tor.onion_service_manager import (
    OnionServiceManager,
)


class FakeClient:

    def __init__(self):
        self.calls = []
        self.connected = False
        self.closed = False

    def connect(self):
        self.connected = True

    def close(self):
        self.connected = False
        self.closed = True

    def add_onion(
        self,
        *,
        key,
        virtual_port,
        target_host,
        target_port,
    ):
        self.calls.append(
            {
                "key": key,
                "virtual_port": virtual_port,
                "target_host": target_host,
                "target_port": target_port,
            }
        )

        return type(
            "OnionService",
            (),
            {
                "service_id": "a" * 56,
                "private_key": (
                    "ED25519-V3:test-private-key"
                ),
            },
        )()

class FakeAuthenticator:

    def __init__(self):
        self.calls = 0

    def authenticate(self):
        self.calls += 1

def test_onion_service_manager_creates_and_persists_identity(
    tmp_path,
):
    identity_file = (
        tmp_path
        / "onion-service.key"
    )

    client = FakeClient()

    manager = OnionServiceManager(
        client=client,
        identity_file=identity_file,
        virtual_port=25,
        target_host="127.0.0.1",
        target_port=2525,
    )

    hostname = manager.ensure_service()

    assert hostname == (
        ("a" * 56)
        + ".onion"
    )

    assert client.calls == [
        {
            "key": "NEW:ED25519-V3",
            "virtual_port": 25,
            "target_host": "127.0.0.1",
            "target_port": 2525,
        }
    ]

    assert identity_file.read_text(
        encoding="utf-8"
    ) == (
        "ED25519-V3:test-private-key"
    )


def test_onion_service_manager_reuses_existing_identity(
    tmp_path,
):
    identity_file = (
        tmp_path
        / "onion-service.key"
    )

    identity_file.write_text(
        "ED25519-V3:existing-private-key",
        encoding="utf-8",
    )

    client = FakeClient()

    manager = OnionServiceManager(
        client=client,
        identity_file=identity_file,
        virtual_port=25,
        target_host="127.0.0.1",
        target_port=2525,
    )

    hostname = manager.ensure_service()

    assert hostname == (
        ("a" * 56)
        + ".onion"
    )

    assert client.calls == [
        {
            "key": (
                "ED25519-V3:"
                "existing-private-key"
            ),
            "virtual_port": 25,
            "target_host": "127.0.0.1",
            "target_port": 2525,
        }
    ]

    assert identity_file.read_text(
        encoding="utf-8"
    ) == (
        "ED25519-V3:"
        "existing-private-key"
    )


def test_onion_service_manager_starts_service(
    tmp_path,
):
    client = FakeClient()
    authenticator = FakeAuthenticator()

    manager = OnionServiceManager(
        client=client,
        authenticator=authenticator,
        identity_file=(
            tmp_path
            / "onion-service.key"
        ),
        virtual_port=25,
        target_host="127.0.0.1",
        target_port=2525,
    )

    manager.start()

    assert client.connected is True
    assert authenticator.calls == 1

    assert manager.hostname == (
        ("a" * 56)
        + ".onion"
    )

    assert len(client.calls) == 1


def test_onion_service_manager_stops_service(
    tmp_path,
):
    client = FakeClient()
    authenticator = FakeAuthenticator()

    manager = OnionServiceManager(
        client=client,
        authenticator=authenticator,
        identity_file=(
            tmp_path
            / "onion-service.key"
        ),
        virtual_port=25,
        target_host="127.0.0.1",
        target_port=2525,
    )

    manager.start()

    assert client.connected is True

    manager.stop()

    assert client.connected is False
    assert client.closed is True


def test_onion_service_manager_publishes_hostname(
    tmp_path,
):
    client = FakeClient()
    authenticator = FakeAuthenticator()

    hostnames = []

    manager = OnionServiceManager(
        client=client,
        authenticator=authenticator,
        identity_file=(
            tmp_path
            / "onion-service.key"
        ),
        virtual_port=25,
        target_host="127.0.0.1",
        target_port=2525,
        hostname_callback=(
            hostnames.append
        ),
    )

    manager.start()

    assert hostnames == [
        ("a" * 56) + ".onion"
    ]

@pytest.mark.skipif(
    os.name == "nt",
    reason="POSIX permission bits are required",
)
def test_onion_service_manager_protects_identity_directory(
    tmp_path,
):
    identity_file = (
        tmp_path
        / "state"
        / "onion-service.key"
    )

    manager = OnionServiceManager(
        client=FakeClient(),
        identity_file=identity_file,
        virtual_port=25,
        target_host="127.0.0.1",
        target_port=2525,
    )

    manager.ensure_service()

    mode = stat.S_IMODE(
        identity_file.parent.stat().st_mode
    )

    assert mode == 0o700


@pytest.mark.skipif(
    os.name == "nt",
    reason="POSIX permission bits are required",
)
def test_onion_service_manager_protects_identity_file(
    tmp_path,
):
    identity_file = (
        tmp_path
        / "state"
        / "onion-service.key"
    )

    manager = OnionServiceManager(
        client=FakeClient(),
        identity_file=identity_file,
        virtual_port=25,
        target_host="127.0.0.1",
        target_port=2525,
    )

    manager.ensure_service()

    mode = stat.S_IMODE(
        identity_file.stat().st_mode
    )

    assert mode == 0o600


@pytest.mark.skipif(
    os.name == "nt",
    reason="POSIX permission bits are required",
)
def test_onion_service_manager_repairs_existing_key_permissions(
    tmp_path,
):
    identity_file = (
        tmp_path
        / "state"
        / "onion-service.key"
    )

    identity_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    identity_file.write_text(
        "ED25519-V3:existing-private-key",
        encoding="utf-8",
    )

    identity_file.chmod(
        0o644
    )

    manager = OnionServiceManager(
        client=FakeClient(),
        identity_file=identity_file,
        virtual_port=25,
        target_host="127.0.0.1",
        target_port=2525,
    )

    manager.ensure_service()

    assert (
        stat.S_IMODE(
            identity_file.stat().st_mode
        )
        == 0o600
    )


@pytest.mark.skipif(
    os.name == "nt",
    reason="Symlink semantics differ on Windows",
)
def test_onion_service_manager_rejects_symlink_identity_file(
    tmp_path,
):
    target = (
        tmp_path
        / "target.key"
    )

    target.write_text(
        "do-not-touch",
        encoding="utf-8",
    )

    identity_file = (
        tmp_path
        / "state"
        / "onion-service.key"
    )

    identity_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    identity_file.symlink_to(
        target
    )

    manager = OnionServiceManager(
        client=FakeClient(),
        identity_file=identity_file,
        virtual_port=25,
        target_host="127.0.0.1",
        target_port=2525,
    )

    with pytest.raises(
        RuntimeError,
        match="symlink",
    ):
        manager.ensure_service()

    assert (
        target.read_text(
            encoding="utf-8"
        )
        == "do-not-touch"
    )


def test_onion_service_manager_leaves_no_temporary_identity_file(
    tmp_path,
):
    identity_file = (
        tmp_path
        / "state"
        / "onion-service.key"
    )

    manager = OnionServiceManager(
        client=FakeClient(),
        identity_file=identity_file,
        virtual_port=25,
        target_host="127.0.0.1",
        target_port=2525,
    )

    manager.ensure_service()

    temporary_files = list(
        identity_file.parent.glob(
            ".onion-service.key.*"
        )
    )

    assert temporary_files == []


@pytest.mark.skipif(
    os.name == "nt",
    reason="POSIX permission bits are required",
)
def test_onion_service_manager_repairs_identity_directory_permissions(
    tmp_path,
):
    state_directory = (
        tmp_path
        / "state"
    )

    state_directory.mkdir()
    state_directory.chmod(
        0o755
    )

    identity_file = (
        state_directory
        / "onion-service.key"
    )

    manager = OnionServiceManager(
        client=FakeClient(),
        identity_file=identity_file,
        virtual_port=25,
        target_host="127.0.0.1",
        target_port=2525,
    )

    manager.ensure_service()

    assert (
        stat.S_IMODE(
            state_directory.stat().st_mode
        )
        == 0o700
    )


def test_onion_service_manager_cleans_temporary_file_if_replace_fails(
    tmp_path,
    monkeypatch,
):
    identity_file = (
        tmp_path
        / "state"
        / "onion-service.key"
    )

    manager = OnionServiceManager(
        client=FakeClient(),
        identity_file=identity_file,
        virtual_port=25,
        target_host="127.0.0.1",
        target_port=2525,
    )

    def fail_replace(
        source,
        destination,
    ):
        raise OSError(
            "simulated replace failure"
        )

    monkeypatch.setattr(
        os,
        "replace",
        fail_replace,
    )

    with pytest.raises(
        OSError,
        match="simulated replace failure",
    ):
        manager.ensure_service()

    assert (
        identity_file.exists()
        is False
    )

    assert list(
        identity_file.parent.glob(
            ".onion-service.key.*"
        )
    ) == []