# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.security.signing_identity import (
    SigningIdentity,
)
import stat
import pytest


def test_signing_identity_persists_private_key(
    tmp_path,
):
    path = tmp_path / "signing.key"

    first = SigningIdentity(path)
    first_public = (
        first.private_key
        .public_key()
        .public_bytes_raw()
    )

    second = SigningIdentity(path)
    second_public = (
        second.private_key
        .public_key()
        .public_bytes_raw()
    )

    assert first_public == second_public


def test_signing_identity_uses_private_permissions(
    tmp_path,
):
    path = tmp_path / "state" / "signing.key"

    SigningIdentity(path)

    directory_mode = stat.S_IMODE(
        path.parent.stat().st_mode
    )

    file_mode = stat.S_IMODE(
        path.stat().st_mode
    )

    assert directory_mode == 0o700
    assert file_mode == 0o600


def test_signing_identity_rejects_symlink(
    tmp_path,
):
    target = tmp_path / "target.key"

    target.write_bytes(
        b"\x01" * 32
    )

    path = tmp_path / "signing.key"
    path.symlink_to(target)

    with pytest.raises(ValueError):
        SigningIdentity(path)


def test_signing_identity_rejects_symlink_created_after_init(
    tmp_path,
):
    path = tmp_path / "signing.key"

    identity = SigningIdentity(path)

    path.unlink()

    target = tmp_path / "target.key"
    target.write_bytes(
        b"\x01" * 32
    )

    path.symlink_to(target)

    with pytest.raises(ValueError):
        identity._save(
            identity.private_key
        )


def test_signing_identity_uses_atomic_replace(
    tmp_path,
    monkeypatch,
):
    path = tmp_path / "state" / "signing.key"

    import garlicsmtp.security.signing_identity as signing_identity_module

    replace_calls = []

    real_replace = signing_identity_module.os.replace

    def tracking_replace(
        source,
        destination,
    ):
        replace_calls.append(
            (
                source,
                destination,
            )
        )

        return real_replace(
            source,
            destination,
        )

    monkeypatch.setattr(
        signing_identity_module.os,
        "replace",
        tracking_replace,
    )

    SigningIdentity(path)

    assert len(replace_calls) == 1

    source, destination = replace_calls[0]

    assert destination == path
    assert source.parent == path.parent
    assert source != path


def test_signing_identity_rejects_invalid_existing_key(
    tmp_path,
):
    path = tmp_path / "signing.key"

    invalid = b"not-a-valid-ed25519-private-key"

    path.write_bytes(
        invalid
    )

    original = path.read_bytes()

    with pytest.raises(ValueError):
        SigningIdentity(path)

    assert path.read_bytes() == original


def test_signing_identity_rejects_wrong_length_key(
    tmp_path,
):
    path = tmp_path / "signing.key"

    invalid = b"\x01" * 31

    path.write_bytes(
        invalid
    )

    original = path.read_bytes()

    with pytest.raises(ValueError):
        SigningIdentity(path)

    assert path.read_bytes() == original