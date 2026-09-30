# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import json
import pytest

from garlicsmtp.application.attachment_limit_admin import (
    AttachmentLimitAdminStore,
)
from garlicsmtp.security.auth.password_hasher import (
    PasswordHasher,
)


def test_attachment_limit_admin_store_creates_hashed_configuration(
    tmp_path,
):
    path = tmp_path / "attachment-limit.json"

    store = AttachmentLimitAdminStore(
        path=path
    )

    store.create(
        password="secret-password"
    )

    data = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    assert data["limit_bytes"] == 1_048_576

    assert (
        data["password_hash"]
        != "secret-password"
    )

    assert PasswordHasher().verify_password(
        "secret-password",
        data["password_hash"],
    )


def test_attachment_limit_admin_store_rejects_wrong_password(
    tmp_path,
):
    path = tmp_path / "attachment-limit.json"

    store = AttachmentLimitAdminStore(
        path=path
    )

    store.create(
        password="secret-password"
    )

    with pytest.raises(PermissionError):
        store.change_limit(
            password="wrong-password",
            limit_bytes=2_097_152,
        )

    data = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    assert data["limit_bytes"] == 1_048_576


def test_attachment_limit_admin_store_changes_limit_with_correct_password(
    tmp_path,
):
    path = tmp_path / "attachment-limit.json"

    store = AttachmentLimitAdminStore(
        path=path
    )

    store.create(
        password="secret-password"
    )

    store.change_limit(
        password="secret-password",
        limit_bytes=2_097_152,
    )

    data = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    assert data["limit_bytes"] == 2_097_152

    assert PasswordHasher().verify_password(
        "secret-password",
        data["password_hash"],
    )


def test_attachment_limit_admin_store_preserves_private_mode_after_change(
    tmp_path,
):
    path = tmp_path / "attachment-limit.json"

    store = AttachmentLimitAdminStore(
        path=path
    )

    store.create(
        password="secret-password"
    )

    store.change_limit(
        password="secret-password",
        limit_bytes=2_097_152,
    )

    assert (
        path.stat().st_mode & 0o777
    ) == 0o600


def test_attachment_limit_admin_store_fails_closed_on_corrupt_json(
    tmp_path,
):
    path = tmp_path / "attachment-limit.json"

    path.write_text(
        "{not-valid-json",
        encoding="utf-8",
    )

    original_content = path.read_text(
        encoding="utf-8"
    )

    store = AttachmentLimitAdminStore(
        path=path
    )

    with pytest.raises(
        json.JSONDecodeError
    ):
        store.change_limit(
            password="secret-password",
            limit_bytes=2_097_152,
        )

    assert path.read_text(
        encoding="utf-8"
    ) == original_content


def test_attachment_limit_admin_store_fails_closed_without_password_hash(
    tmp_path,
):
    path = tmp_path / "attachment-limit.json"

    data = {
        "limit_bytes": 1_048_576,
    }

    path.write_text(
        json.dumps(data),
        encoding="utf-8",
    )

    original_content = path.read_text(
        encoding="utf-8"
    )

    store = AttachmentLimitAdminStore(
        path=path
    )

    with pytest.raises(
        KeyError
    ):
        store.change_limit(
            password="secret-password",
            limit_bytes=2_097_152,
        )

    assert path.read_text(
        encoding="utf-8"
    ) == original_content


@pytest.mark.parametrize(
    "invalid_limit",
    [
        0,
        -1,
        True,
        False,
        1.5,
        "2097152",
        None,
    ],
)
def test_attachment_limit_admin_store_rejects_invalid_limits(
    tmp_path,
    invalid_limit,
):
    path = tmp_path / "attachment-limit.json"

    store = AttachmentLimitAdminStore(
        path=path
    )

    store.create(
        password="secret-password"
    )

    with pytest.raises(ValueError):
        store.change_limit(
            password="secret-password",
            limit_bytes=invalid_limit,
        )

    data = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    assert data["limit_bytes"] == 1_048_576