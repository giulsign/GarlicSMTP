# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import stat
import pytest
from garlicsmtp.security.encryption_identity import (
    EncryptionIdentity,
)


def test_encryption_identity_persists_private_key(
    tmp_path,
):
    path = tmp_path / "encryption.key"

    first = EncryptionIdentity(path)
    first_public = (
        first.private_key
        .public_key()
        .public_bytes_raw()
    )

    second = EncryptionIdentity(path)
    second_public = (
        second.private_key
        .public_key()
        .public_bytes_raw()
    )

    assert first_public == second_public


def test_encryption_identity_uses_private_permissions(
    tmp_path,
):
    path = tmp_path / "state" / "encryption.key"

    EncryptionIdentity(path)

    directory_mode = stat.S_IMODE(
        path.parent.stat().st_mode
    )

    file_mode = stat.S_IMODE(
        path.stat().st_mode
    )

    assert directory_mode == 0o700
    assert file_mode == 0o600


def test_encryption_identity_rejects_symlink(
    tmp_path,
):
    target = tmp_path / "target.key"

    target.write_bytes(
        b"\x01" * 32
    )

    path = tmp_path / "encryption.key"
    path.symlink_to(target)

    with pytest.raises(ValueError):
        EncryptionIdentity(path)


def test_encryption_identity_rejects_symlink_created_after_init(
    tmp_path,
):
    path = tmp_path / "encryption.key"

    identity = EncryptionIdentity(path)

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


def test_encryption_identity_uses_atomic_replace(
    tmp_path,
    monkeypatch,
):
    path = tmp_path / "state" / "encryption.key"

    import garlicsmtp.security.encryption_identity as encryption_identity_module

    replace_calls = []

    real_replace = encryption_identity_module.os.replace

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
        encryption_identity_module.os,
        "replace",
        tracking_replace,
    )

    EncryptionIdentity(path)

    assert len(replace_calls) == 1

    source, destination = replace_calls[0]

    assert destination == path
    assert source.parent == path.parent
    assert source != path


def test_encryption_identity_rejects_invalid_existing_key(
    tmp_path,
):
    path = tmp_path / "encryption.key"

    invalid = b"not-a-valid-x25519-private-key"

    path.write_bytes(
        invalid
    )

    original = path.read_bytes()

    with pytest.raises(ValueError):
        EncryptionIdentity(path)

    assert path.read_bytes() == original


def test_encryption_identity_rejects_wrong_length_key(
    tmp_path,
):
    path = tmp_path / "encryption.key"

    invalid = b"\x01" * 31

    path.write_bytes(
        invalid
    )

    original = path.read_bytes()

    with pytest.raises(ValueError):
        EncryptionIdentity(path)

    assert path.read_bytes() == original


def test_encryption_identity_repairs_existing_key_permissions(
    tmp_path,
):
    path = tmp_path / "encryption.key"

    identity = EncryptionIdentity(path)

    path.chmod(
        0o644
    )

    EncryptionIdentity(path)

    file_mode = stat.S_IMODE(
        path.stat().st_mode
    )

    assert file_mode == 0o600


def test_encryption_identity_repairs_existing_directory_permissions(
    tmp_path,
):
    directory = tmp_path / "state"
    path = directory / "encryption.key"

    EncryptionIdentity(path)

    directory.chmod(
        0o755
    )

    EncryptionIdentity(path)

    directory_mode = stat.S_IMODE(
        directory.stat().st_mode
    )

    assert directory_mode == 0o700