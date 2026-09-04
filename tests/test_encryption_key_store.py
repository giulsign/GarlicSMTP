# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import pytest
import stat
import os

from garlicsmtp.security.encryption_key_store import (
    MemoryEncryptionKeyStore,
)
from garlicsmtp.security.encryption_key_store import (
    FileEncryptionKeyStore,
)


def test_encryption_key_store_rejects_changed_key():
    store = MemoryEncryptionKeyStore()

    host = "a" * 56 + ".onion"

    first_key = b"\x01" * 32
    changed_key = b"\x02" * 32

    store.remember(
        host,
        first_key,
    )

    with pytest.raises(
        ValueError,
        match="encryption key changed",
    ):
        store.remember(
            host,
            changed_key,
        )

    assert store.get(host) == first_key


def test_encryption_key_store_accepts_same_key_again():
    store = MemoryEncryptionKeyStore()

    host = "a" * 56 + ".onion"
    key = b"\x01" * 32

    store.remember(
        host,
        key,
    )

    store.remember(
        host,
        key,
    )

    assert store.get(host) == key


def test_encryption_key_store_returns_none_for_unknown_host():
    store = MemoryEncryptionKeyStore()

    host = "a" * 56 + ".onion"

    assert store.get(host) is None



def test_file_encryption_key_store_persists_host_key(
    tmp_path,
):
    path = (
        tmp_path
        / "encryption_keys.json"
    )

    host = "a" * 56 + ".onion"
    key = b"\x01" * 32

    store = FileEncryptionKeyStore(
        path
    )

    store.remember(
        host,
        key,
    )

    reloaded = FileEncryptionKeyStore(
        path
    )

    assert (
        reloaded.get(host)
        == key
    )


def test_file_encryption_key_store_uses_private_permissions(
    tmp_path,
):
    path = (
        tmp_path
        / "state"
        / "encryption_keys.json"
    )

    store = FileEncryptionKeyStore(
        path
    )

    store.remember(
        "a" * 56 + ".onion",
        b"\x01" * 32,
    )

    directory_mode = stat.S_IMODE(
        path.parent.stat().st_mode
    )

    file_mode = stat.S_IMODE(
        path.stat().st_mode
    )

    assert directory_mode == 0o700
    assert file_mode == 0o600


def test_file_encryption_key_store_rejects_symlink(
    tmp_path,
):
    target = tmp_path / "target.json"

    target.write_text(
        "{}",
        encoding="utf-8",
    )

    path = (
        tmp_path
        / "encryption_keys.json"
    )

    path.symlink_to(target)

    with pytest.raises(ValueError):
        FileEncryptionKeyStore(path)


def test_file_encryption_key_store_rejects_symlink_created_after_init(
    tmp_path,
):
    path = (
        tmp_path
        / "encryption_keys.json"
    )

    store = FileEncryptionKeyStore(
        path
    )

    target = tmp_path / "target.json"

    target.write_text(
        "{}",
        encoding="utf-8",
    )

    path.symlink_to(target)

    with pytest.raises(ValueError):
        store.remember(
            "a" * 56 + ".onion",
            b"\x01" * 32,
        )


def test_file_encryption_key_store_uses_atomic_replace(
    tmp_path,
    monkeypatch,
):
    path = (
        tmp_path
        / "state"
        / "encryption_keys.json"
    )

    store = FileEncryptionKeyStore(
        path
    )

    replace_calls = []

    import garlicsmtp.security.encryption_key_store as key_store_module

    real_replace = key_store_module.os.replace

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
        key_store_module.os,
        "replace",
        tracking_replace,
    )

    store.remember(
        "a" * 56 + ".onion",
        b"\x01" * 32,
    )

    assert len(replace_calls) == 1

    source, destination = replace_calls[0]

    assert destination == path
    assert source.parent == path.parent
    assert source != path


def test_file_encryption_key_store_rejects_changed_key_after_reload(
    tmp_path,
):
    path = (
        tmp_path
        / "encryption_keys.json"
    )

    host = "a" * 56 + ".onion"

    first_key = b"\x01" * 32
    changed_key = b"\x02" * 32

    store = FileEncryptionKeyStore(
        path
    )

    store.remember(
        host,
        first_key,
    )

    reloaded = FileEncryptionKeyStore(
        path
    )

    with pytest.raises(
        ValueError,
        match="encryption key changed",
    ):
        reloaded.remember(
            host,
            changed_key,
        )

    assert (
        reloaded.get(host)
        == first_key
    )