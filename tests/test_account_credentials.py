# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.


import pytest
import json


from garlicsmtp.security.auth.account_credentials import (
    AccountCredentialStore,
)
from garlicsmtp.security.auth.password_hasher import (
    PasswordHasher,
)


def test_account_credential_store_creates_account_with_hashed_password(
    tmp_path,
):
    path = tmp_path / "account-credentials.json"

    store = AccountCredentialStore(
        path=path,
    )

    store.create(
        username="alice",
        password="Garlic1!",
    )

    assert path.exists()

    data = json.loads(
        path.read_text(
            encoding="utf-8",
        )
    )

    assert data["username"] == "alice"
    assert "password_hash" in data
    assert data["password_hash"] != "Garlic1!"

    assert PasswordHasher().verify_password(
        "Garlic1!",
        data["password_hash"],
    ) is True



def test_account_credential_store_rejects_empty_username(
    tmp_path,
):
    path = tmp_path / "account-credentials.json"

    store = AccountCredentialStore(
        path=path,
    )

    with pytest.raises(
        ValueError,
    ):
        store.create(
            username="",
            password="Garlic1!",
        )

    assert not path.exists()


def test_account_credential_store_rejects_blank_username(
    tmp_path,
):
    path = tmp_path / "account-credentials.json"

    store = AccountCredentialStore(
        path=path,
    )

    with pytest.raises(
        ValueError,
    ):
        store.create(
            username="   ",
            password="Garlic1!",
        )

    assert not path.exists()


def test_account_credential_store_rejects_password_shorter_than_eight_characters(
    tmp_path,
):
    path = tmp_path / "account-credentials.json"

    store = AccountCredentialStore(
        path=path,
    )

    with pytest.raises(
        ValueError,
    ):
        store.create(
            username="alice",
            password="Gar1!ab",
        )

    assert not path.exists()


def test_account_credential_store_rejects_password_without_uppercase(
    tmp_path,
):
    path = tmp_path / "account-credentials.json"

    store = AccountCredentialStore(
        path=path,
    )

    with pytest.raises(
        ValueError,
    ):
        store.create(
            username="alice",
            password="garlic1!",
        )

    assert not path.exists()


def test_account_credential_store_rejects_password_without_digit(
    tmp_path,
):
    path = tmp_path / "account-credentials.json"

    store = AccountCredentialStore(
        path=path,
    )

    with pytest.raises(
        ValueError,
    ):
        store.create(
            username="alice",
            password="Garlic!!",
        )

    assert not path.exists()


def test_account_credential_store_rejects_password_without_special_character(
    tmp_path,
):
    path = tmp_path / "account-credentials.json"

    store = AccountCredentialStore(
        path=path,
    )

    with pytest.raises(
        ValueError,
    ):
        store.create(
            username="alice",
            password="Garlic12",
        )

    assert not path.exists()


def test_account_credential_store_creates_credentials_with_private_permissions(
    tmp_path,
):
    path = tmp_path / "account-credentials.json"

    store = AccountCredentialStore(
        path=path,
    )

    store.create(
        username="alice",
        password="Garlic1!",
    )

    assert (
        path.stat().st_mode & 0o777
    ) == 0o600


def test_account_credential_store_does_not_overwrite_existing_account(
    tmp_path,
):
    path = tmp_path / "account-credentials.json"

    store = AccountCredentialStore(
        path=path,
    )

    store.create(
        username="alice",
        password="Garlic1!",
    )

    original_content = path.read_text(
        encoding="utf-8",
    )

    with pytest.raises(
        FileExistsError,
    ):
        store.create(
            username="bob",
            password="Different2!",
        )

    assert path.read_text(
        encoding="utf-8",
    ) == original_content


def test_account_credential_store_authenticates_valid_credentials(
    tmp_path,
):
    path = tmp_path / "account-credentials.json"

    store = AccountCredentialStore(
        path=path,
    )

    store.create(
        username="alice",
        password="Garlic1!",
    )

    assert store.authenticate(
        username="alice",
        password="Garlic1!",
    ) is True


def test_account_credential_store_rejects_invalid_password(
    tmp_path,
):
    path = tmp_path / "account-credentials.json"

    store = AccountCredentialStore(
        path=path,
    )

    store.create(
        username="alice",
        password="Garlic1!",
    )

    assert store.authenticate(
        username="alice",
        password="Wrong2!",
    ) is False


def test_account_credential_store_rejects_invalid_username(
    tmp_path,
):
    path = tmp_path / "account-credentials.json"

    store = AccountCredentialStore(
        path=path,
    )

    store.create(
        username="alice",
        password="Garlic1!",
    )

    assert store.authenticate(
        username="bob",
        password="Garlic1!",
    ) is False


def test_account_credential_store_rejects_corrupt_credentials(
    tmp_path,
):
    path = tmp_path / "account-credentials.json"

    path.write_text(
        "{not-valid-json",
        encoding="utf-8",
    )
    path.chmod(0o600)

    store = AccountCredentialStore(
        path=path,
    )

    with pytest.raises(
        ValueError,
        match="Invalid account credentials",
    ):
        store.authenticate(
            username="alice",
            password="Garlic1!",
        )


def test_account_credential_store_rejects_structurally_invalid_credentials(
    tmp_path,
):
    path = tmp_path / "account-credentials.json"

    path.write_text(
        json.dumps(
            {
                "username": "alice",
            }
        ),
        encoding="utf-8",
    )
    path.chmod(0o600)

    store = AccountCredentialStore(
        path=path,
    )

    with pytest.raises(
        ValueError,
        match="Invalid account credentials",
    ):
        store.authenticate(
            username="alice",
            password="Garlic1!",
        )


def test_account_credential_store_rejects_malformed_password_hash(
    tmp_path,
):
    path = tmp_path / "account-credentials.json"

    path.write_text(
        json.dumps(
            {
                "username": "alice",
                "password_hash": (
                    "not-a-valid-password-hash"
                ),
            }
        ),
        encoding="utf-8",
    )
    path.chmod(0o600)

    store = AccountCredentialStore(
        path=path,
    )

    with pytest.raises(
        ValueError,
        match="Invalid account credentials",
    ):
        store.authenticate(
            username="alice",
            password="Garlic1!",
        )


def test_account_credential_store_rejects_insecure_permissions(
    tmp_path,
):
    path = tmp_path / "account-credentials.json"

    store = AccountCredentialStore(
        path=path,
    )

    store.create(
        username="alice",
        password="Garlic1!",
    )

    path.chmod(0o644)

    with pytest.raises(
        PermissionError,
        match="Insecure account credentials permissions",
    ):
        store.authenticate(
            username="alice",
            password="Garlic1!",
        )


def test_account_credential_store_rejects_symlink(
    tmp_path,
):
    target = tmp_path / "real-account-credentials.json"

    AccountCredentialStore(
        path=target,
    ).create(
        username="alice",
        password="Garlic1!",
    )

    path = tmp_path / "account-credentials.json"
    path.symlink_to(target)

    store = AccountCredentialStore(
        path=path,
    )

    with pytest.raises(
        ValueError,
        match="Invalid account credentials",
    ):
        store.authenticate(
            username="alice",
            password="Garlic1!",
        )