# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0

# See LICENSE for the full license terms.

import os

import json

import pytest

from garlicsmtp.security.auth.imap_credentials import (
    ImapCredentialStore,
)
from garlicsmtp.security.auth.persistent_imap_authenticator import (
    PersistentImapAuthenticator,
)
from garlicsmtp.security.auth.password_hasher import (
    PasswordHasher,
)


def test_persistent_imap_authenticator_accepts_valid_credentials(
    tmp_path,
):
    path = tmp_path / "imap-credentials.json"

    ImapCredentialStore(
        path=path,
    ).create(
        username="garlicsmtp",
        password="secret-password",
    )

    authenticator = PersistentImapAuthenticator(
        path=path,
    )

    assert authenticator.authenticate(
        "garlicsmtp",
        "secret-password",
    ) is True


def test_persistent_imap_authenticator_rejects_wrong_password(
    tmp_path,
):
    path = tmp_path / "imap-credentials.json"

    ImapCredentialStore(
        path=path,
    ).create(
        username="garlicsmtp",
        password="secret-password",
    )

    authenticator = PersistentImapAuthenticator(
        path=path,
    )

    assert authenticator.authenticate(
        "garlicsmtp",
        "wrong-password",
    ) is False


def test_persistent_imap_authenticator_rejects_corrupt_credentials(
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

    authenticator = PersistentImapAuthenticator(
        path=path,
    )

    with pytest.raises(
        ValueError,
    ):
        authenticator.authenticate(
            "garlicsmtp",
            "secret-password",
        )


def test_persistent_imap_authenticator_rejects_invalid_json(
    tmp_path,
):
    path = tmp_path / "imap-credentials.json"

    path.write_text(
        "{not-valid-json",
        encoding="utf-8",
    )

    path.chmod(0o600)

    authenticator = PersistentImapAuthenticator(
        path=path,
    )

    with pytest.raises(
        ValueError,
        match="Invalid IMAP credentials",
    ):
        authenticator.authenticate(
            "garlicsmtp",
            "secret-password",
        )



def test_persistent_imap_authenticator_rejects_insecure_permissions(
    tmp_path,
):
    path = tmp_path / "imap-credentials.json"

    ImapCredentialStore(
        path=path,
    ).create(
        username="garlicsmtp",
        password="secret-password",
    )

    os.chmod(
        path,
        0o644,
    )

    authenticator = PersistentImapAuthenticator(
        path=path,
    )

    with pytest.raises(
        PermissionError,
    ):
        authenticator.authenticate(
            "garlicsmtp",
            "secret-password",
        )


def test_persistent_imap_authenticator_rejects_wrong_username(
    tmp_path,
):
    path = tmp_path / "imap-credentials.json"

    ImapCredentialStore(
        path=path,
    ).create(
        username="garlicsmtp",
        password="secret-password",
    )

    authenticator = PersistentImapAuthenticator(
        path=path,
    )

    assert authenticator.authenticate(
        "alice",
        "secret-password",
    ) is False


def test_persistent_imap_authenticator_rejects_malformed_password_hash(
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

    authenticator = PersistentImapAuthenticator(
        path=path,
    )

    with pytest.raises(
        ValueError,
        match="Invalid IMAP credentials",
    ):
        authenticator.authenticate(
            "garlicsmtp",
            "secret-password",
        )


def test_persistent_imap_authenticator_rejects_symlink(
    tmp_path,
):
    target = tmp_path / "target.json"
    target.write_text(
        json.dumps(
            {
                "username": "garlicsmtp",
                "password_hash": (
                    PasswordHasher().hash_password(
                        "secret-password"
                    )
                ),
            }
        ),
        encoding="utf-8",
    )
    target.chmod(0o600)

    path = tmp_path / "imap-credentials.json"
    path.symlink_to(target)

    authenticator = PersistentImapAuthenticator(
        path=path,
    )

    with pytest.raises(
        ValueError,
        match="Invalid IMAP credentials",
    ):
        authenticator.authenticate(
            "garlicsmtp",
            "secret-password",
        )


def test_persistent_imap_authenticator_rejects_noncanonical_stored_username(
    tmp_path,
):
    path = tmp_path / "imap-credentials.json"

    path.write_text(
        json.dumps(
            {
                "username": "alice",
                "password_hash": (
                    PasswordHasher().hash_password(
                        "secret-password"
                    )
                ),
            }
        ),
        encoding="utf-8",
    )
    path.chmod(0o600)

    authenticator = PersistentImapAuthenticator(
        path=path,
    )

    with pytest.raises(
        ValueError,
        match="Invalid IMAP credentials",
    ):
        authenticator.authenticate(
            "garlicsmtp",
            "secret-password",
        )