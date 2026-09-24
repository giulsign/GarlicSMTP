# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.security.trust_store import (
    FileTrustStore,
)
import stat
import pytest
import os
import tempfile


def test_file_trust_store_persists_trusted_sender_key(
    tmp_path,
):
    path = tmp_path / "trusted_keys.json"

    key = b"\x01" * 32

    store = FileTrustStore(path)

    store.trust(
        "alice@test.onion",
        key,
    )

    reloaded = FileTrustStore(path)

    assert (
        reloaded.is_trusted(
            "alice@test.onion",
            key,
        )
        is True
    )



def test_file_trust_store_uses_private_permissions(
    tmp_path,
):
    path = tmp_path / "state" / "trusted_keys.json"

    store = FileTrustStore(path)

    store.trust(
        "alice@test.onion",
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



def test_file_trust_store_rejects_symlink(
    tmp_path,
):
    target = tmp_path / "target.json"

    target.write_text(
        "{}",
        encoding="utf-8",
    )

    path = tmp_path / "trusted_keys.json"
    path.symlink_to(target)

    with pytest.raises(ValueError):
        FileTrustStore(path)


def test_file_trust_store_rejects_symlink_created_after_init(
    tmp_path,
):
    path = tmp_path / "trusted_keys.json"

    store = FileTrustStore(path)

    target = tmp_path / "target.json"
    target.write_text(
        "{}",
        encoding="utf-8",
    )

    path.symlink_to(target)

    with pytest.raises(ValueError):
        store.trust(
            "alice@test.onion",
            b"\x01" * 32,
        )


def test_file_trust_store_uses_atomic_replace(
    tmp_path,
    monkeypatch,
):
    path = tmp_path / "state" / "trusted_keys.json"

    store = FileTrustStore(path)

    replace_calls = []

    import garlicsmtp.security.trust_store as trust_store_module

    real_replace = trust_store_module.os.replace

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
        trust_store_module.os,
        "replace",
        tracking_replace,
    )

    store.trust(
        "alice@test.onion",
        b"\x01" * 32,
    )

    assert len(replace_calls) == 1

    source, destination = replace_calls[0]

    assert destination == path
    assert source.parent == path.parent
    assert source != path