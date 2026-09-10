# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0

# See LICENSE for the full license terms.

import pytest
import json
import stat

from garlicsmtp.security.auth.password_hasher import (
    PasswordHasher,
)
from garlicsmtp.security.auth.imap_credentials import (
    ImapCredentialStore,
)
from garlicsmtp.security.auth.persistent_imap_authenticator import (
    PersistentImapAuthenticator,
)


def test_imap_credential_store_creates_credentials(
    tmp_path,
):
    path = tmp_path / "imap-credentials.json"

    store = ImapCredentialStore(
        path=path,
    )

    store.create(
        username="garlicsmtp",
        password="secret-password",
    )

    assert path.exists()


def test_imap_credential_store_persists_hashed_password(
    tmp_path,
):
    path = tmp_path / "imap-credentials.json"

    store = ImapCredentialStore(
        path=path,
    )

    store.create(
        username="garlicsmtp",
        password="secret-password",
    )

    data = json.loads(
        path.read_text(encoding="utf-8")
    )

    assert data["username"] == "garlicsmtp"
    assert "password_hash" in data
    assert data["password_hash"] != "secret-password"

    assert PasswordHasher().verify_password(
        "secret-password",
        data["password_hash"],
    ) is True


def test_imap_credential_store_does_not_overwrite_existing_credentials(
    tmp_path,
):
    path = tmp_path / "imap-credentials.json"

    store = ImapCredentialStore(
        path=path,
    )

    store.create(
        username="garlicsmtp",
        password="first-password",
    )

    original = path.read_bytes()

    with pytest.raises(
        FileExistsError,
    ):
        store.create(
            username="garlicsmtp",
            password="second-password",
        )

    assert path.read_bytes() == original


def test_imap_credential_store_creates_file_with_restrictive_permissions(
    tmp_path,
):
    path = tmp_path / "imap-credentials.json"

    store = ImapCredentialStore(
        path=path,
    )

    store.create(
        username="garlicsmtp",
        password="secret-password",
    )

    mode = stat.S_IMODE(
        path.stat().st_mode
    )

    assert mode == 0o600


def test_imap_credential_store_rejects_noncanonical_username(
    tmp_path,
):
    path = tmp_path / "imap-credentials.json"

    store = ImapCredentialStore(
        path=path,
    )

    with pytest.raises(
        ValueError,
    ):
        store.create(
            username="alice",
            password="secret-password",
        )

    assert not path.exists()


def test_imap_credential_store_creation_is_exclusive(
    tmp_path,
    monkeypatch,
):
    path = tmp_path / "imap-credentials.json"

    path.write_text(
        "existing-credentials",
        encoding="utf-8",
    )
    original = path.read_bytes()

    original_exists = type(path).exists

    def pretend_absent(self):
        if self == path:
            return False

        return original_exists(self)

    monkeypatch.setattr(
        type(path),
        "exists",
        pretend_absent,
    )

    store = ImapCredentialStore(
        path=path,
    )

    with pytest.raises(
        FileExistsError,
    ):
        store.create(
            username="garlicsmtp",
            password="new-password",
        )

    assert path.read_bytes() == original


def test_imap_credential_store_resets_password(
    tmp_path,
):
    path = tmp_path / "imap-credentials.json"

    store = ImapCredentialStore(
        path=path,
    )

    store.create(
        username="garlicsmtp",
        password="old-password",
    )

    store.reset_password(
        password="new-password",
    )

    authenticator = PersistentImapAuthenticator(
        path=path,
    )

    assert authenticator.authenticate(
        "garlicsmtp",
        "old-password",
    ) is False

    assert authenticator.authenticate(
        "garlicsmtp",
        "new-password",
    ) is True   


def test_imap_credential_store_reset_rejects_corrupt_credentials(
    tmp_path,
):
    path = tmp_path / "imap-credentials.json"

    path.write_text(
        "{not-valid-json",
        encoding="utf-8",
    )
    path.chmod(0o600)

    original = path.read_bytes()

    store = ImapCredentialStore(
        path=path,
    )

    with pytest.raises(
        ValueError,
        match="Invalid IMAP credentials",
    ):
        store.reset_password(
            password="new-password",
        )

    assert path.read_bytes() == original


def test_imap_credential_store_reset_rejects_structurally_invalid_credentials(
    tmp_path,
):
    path = tmp_path / "imap-credentials.json"

    path.write_text(
        json.dumps(
            {
                "username": "garlicsmtp",
            }
        ),
        encoding="utf-8",
    )
    path.chmod(0o600)

    original = path.read_bytes()

    store = ImapCredentialStore(
        path=path,
    )

    with pytest.raises(
        ValueError,
        match="Invalid IMAP credentials",
    ):
        store.reset_password(
            password="new-password",
        )

    assert path.read_bytes() == original


def test_imap_credential_store_reset_rejects_noncanonical_username(
    tmp_path,
):
    path = tmp_path / "imap-credentials.json"

    path.write_text(
        json.dumps(
            {
                "username": "alice",
                "password_hash": (
                    PasswordHasher().hash_password(
                        "old-password"
                    )
                ),
            }
        ),
        encoding="utf-8",
    )
    path.chmod(0o600)

    original = path.read_bytes()

    store = ImapCredentialStore(
        path=path,
    )

    with pytest.raises(
        ValueError,
        match="Invalid IMAP credentials",
    ):
        store.reset_password(
            password="new-password",
        )

    assert path.read_bytes() == original


def test_imap_credential_store_reset_rejects_malformed_password_hash(
    tmp_path,
):
    path = tmp_path / "imap-credentials.json"

    path.write_text(
        json.dumps(
            {
                "username": "garlicsmtp",
                "password_hash": "not-a-valid-password-hash",
            }
        ),
        encoding="utf-8",
    )
    path.chmod(0o600)

    original = path.read_bytes()

    store = ImapCredentialStore(
        path=path,
    )

    with pytest.raises(
        ValueError,
        match="Invalid IMAP credentials",
    ):
        store.reset_password(
            password="new-password",
        )

    assert path.read_bytes() == original


def test_imap_credential_store_reset_rejects_insecure_permissions(
    tmp_path,
):
    path = tmp_path / "imap-credentials.json"

    store = ImapCredentialStore(
        path=path,
    )

    store.create(
        username="garlicsmtp",
        password="old-password",
    )

    path.chmod(0o644)
    original = path.read_bytes()

    with pytest.raises(
        PermissionError,
    ):
        store.reset_password(
            password="new-password",
        )

    assert path.read_bytes() == original