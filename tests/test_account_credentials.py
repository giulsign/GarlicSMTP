# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import os
import stat
import pytest
import json
from pathlib import Path
import garlicsmtp.security.auth.account_credentials as module


from garlicsmtp.security.auth.account_credentials import (
    AccountCredentialStore,
)
from garlicsmtp.security.auth.password_hasher import (
    PasswordHasher,
)
from garlicsmtp.security.at_rest_key_manager import AtRestKeyManager
from cryptography.exceptions import InvalidTag



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


def test_account_credential_store_creates_private_file_before_writing(
    tmp_path,
    monkeypatch,
):
    path = tmp_path / "account-credentials.json"
    store = AccountCredentialStore(path=path)

    original_open = os.open
    permissions_during_write = []

    def inspect_open(file, flags, mode=0o777, *, dir_fd=None):
        if dir_fd is None:
            descriptor = original_open(file, flags, mode)
        else:
            descriptor = original_open(
                file,
                flags,
                mode,
                dir_fd=dir_fd,
            )

        if os.fspath(file) == os.fspath(path):
            permissions_during_write.append(
                stat.S_IMODE(os.fstat(descriptor).st_mode)
            )

        return descriptor

    monkeypatch.setattr(os, "open", inspect_open)

    original_umask = os.umask(0)
    try:
        store.create(
            username="alice",
            password="Garlic1!",
        )
    finally:
        os.umask(original_umask)

    assert permissions_during_write == [0o600]


def test_existing_account_can_enable_recovery_without_recreating_account(
    tmp_path,
):

    path = tmp_path / "account-credentials.json"
    store = AccountCredentialStore(path=path)

    store.create(
        username="alice",
        password="Garlic1!",
    )

    original = json.loads(path.read_text(encoding="utf-8"))
    original_password_hash = original["password_hash"]

    manager = AtRestKeyManager()
    recovery_key = manager.generate_recovery_key()

    store.enable_recovery(
        username="alice",
        password="Garlic1!",
        recovery_key=recovery_key,
    )

    updated = json.loads(path.read_text(encoding="utf-8"))

    assert updated["username"] == "alice"
    assert updated["password_hash"] == original_password_hash
    assert updated["wrapped_dek_password"]
    assert updated["wrapped_dek_recovery"]

    assert "Garlic1!" not in path.read_text(encoding="utf-8")
    assert recovery_key not in path.read_text(encoding="utf-8")

    assert store.authenticate(
        username="alice",
        password="Garlic1!",
    ) is True

    assert store.unlock_dek_with_password(
        username="alice",
        password="Garlic1!",
    ) == store.unlock_dek_with_recovery(
        username="alice",
        recovery_key=recovery_key,
    )


def test_recovery_reset_changes_password_but_preserves_dek(tmp_path):

    path = tmp_path / "account-credentials.json"
    store = AccountCredentialStore(path=path)
    store.create(username="alice", password="Garlic1!")

    manager = AtRestKeyManager()
    old_recovery = manager.generate_recovery_key()
    new_recovery = manager.generate_recovery_key()

    store.enable_recovery(
        username="alice",
        password="Garlic1!",
        recovery_key=old_recovery,
    )

    original_dek = store.unlock_dek_with_password(
        username="alice",
        password="Garlic1!",
    )

    store.reset_password_with_recovery(
        username="alice",
        recovery_key=old_recovery,
        new_password="NewGarlic2!",
        new_recovery_key=new_recovery,
    )

    assert not store.authenticate(
        username="alice",
        password="Garlic1!",
    )
    assert store.authenticate(
        username="alice",
        password="NewGarlic2!",
    )
    assert store.unlock_dek_with_password(
        username="alice",
        password="NewGarlic2!",
    ) == original_dek
    assert store.unlock_dek_with_recovery(
        username="alice",
        recovery_key=new_recovery,
    ) == original_dek


def test_recovery_reset_invalidates_old_recovery_key(tmp_path):

    path = tmp_path / "account-credentials.json"
    store = AccountCredentialStore(path=path)
    store.create(username="alice", password="Garlic1!")

    manager = AtRestKeyManager()
    old_key = manager.generate_recovery_key()
    new_key = manager.generate_recovery_key()

    store.enable_recovery(
        username="alice",
        password="Garlic1!",
        recovery_key=old_key,
    )

    store.reset_password_with_recovery(
        username="alice",
        recovery_key=old_key,
        new_password="NewGarlic2!",
        new_recovery_key=new_key,
    )

    with pytest.raises((InvalidTag, ValueError)):
        store.unlock_dek_with_recovery(
            username="alice",
            recovery_key=old_key,
        )


def test_recovery_reset_rejects_wrong_key_without_changes(tmp_path):

    path = tmp_path / "account-credentials.json"
    store = AccountCredentialStore(path=path)
    store.create(username="alice", password="Garlic1!")

    recovery_key = AtRestKeyManager().generate_recovery_key()
    store.enable_recovery(
        username="alice",
        password="Garlic1!",
        recovery_key=recovery_key,
    )

    original_content = path.read_bytes()

    with pytest.raises((InvalidTag, ValueError)):
        store.reset_password_with_recovery(
            username="alice",
            recovery_key="incorrect-recovery-key",
            new_password="NewGarlic2!",
            new_recovery_key=AtRestKeyManager().generate_recovery_key(),
        )

    assert path.read_bytes() == original_content


def test_recovery_reset_rejects_weak_new_password(tmp_path):

    path = tmp_path / "account-credentials.json"
    store = AccountCredentialStore(path=path)
    store.create(username="alice", password="Garlic1!")

    recovery_key = AtRestKeyManager().generate_recovery_key()
    store.enable_recovery(
        username="alice",
        password="Garlic1!",
        recovery_key=recovery_key,
    )

    original_content = path.read_bytes()

    with pytest.raises(ValueError):
        store.reset_password_with_recovery(
            username="alice",
            recovery_key=recovery_key,
            new_password="weak",
            new_recovery_key=AtRestKeyManager().generate_recovery_key(),
        )

    assert path.read_bytes() == original_content


def test_recovery_reset_survives_store_reopening(tmp_path):

    path = tmp_path / "account-credentials.json"
    store = AccountCredentialStore(path=path)
    store.create(username="alice", password="Garlic1!")

    manager = AtRestKeyManager()
    old_key = manager.generate_recovery_key()
    new_key = manager.generate_recovery_key()

    store.enable_recovery(
        username="alice",
        password="Garlic1!",
        recovery_key=old_key,
    )

    original_dek = store.unlock_dek_with_password(
        username="alice",
        password="Garlic1!",
    )

    store.reset_password_with_recovery(
        username="alice",
        recovery_key=old_key,
        new_password="NewGarlic2!",
        new_recovery_key=new_key,
    )

    reopened = AccountCredentialStore(path=path)

    assert reopened.authenticate(
        username="alice",
        password="NewGarlic2!",
    )
    assert reopened.unlock_dek_with_password(
        username="alice",
        password="NewGarlic2!",
    ) == original_dek


def test_recovery_enable_write_failure_preserves_credentials(
    tmp_path, monkeypatch,
):

    path = tmp_path / "account-credentials.json"
    store = AccountCredentialStore(path=path)
    store.create(username="alice", password="Garlic1!")

    original = path.read_bytes()

    def fail_replace(source, destination):
        raise OSError("Simulated replace failure")

    monkeypatch.setattr(module.os, "replace", fail_replace)

    with pytest.raises(OSError, match="Simulated replace failure"):
        store.enable_recovery(
            username="alice",
            password="Garlic1!",
            recovery_key=AtRestKeyManager().generate_recovery_key(),
        )

    assert path.read_bytes() == original
    assert store.authenticate(
        username="alice",
        password="Garlic1!",
    )
    assert not list(tmp_path.glob(".account-credentials-*.tmp"))


def test_recovery_reset_replace_failure_preserves_old_keys(
    tmp_path, monkeypatch,
):

    path = tmp_path / "account-credentials.json"
    store = AccountCredentialStore(path=path)
    store.create(username="alice", password="Garlic1!")

    manager = AtRestKeyManager()
    old_key = manager.generate_recovery_key()

    store.enable_recovery(
        username="alice",
        password="Garlic1!",
        recovery_key=old_key,
    )

    original = path.read_bytes()
    original_dek = store.unlock_dek_with_recovery(
        username="alice",
        recovery_key=old_key,
    )

    def fail_replace(source, destination):
        raise OSError("Simulated replace failure")

    monkeypatch.setattr(module.os, "replace", fail_replace)

    with pytest.raises(OSError, match="Simulated replace failure"):
        store.reset_password_with_recovery(
            username="alice",
            recovery_key=old_key,
            new_password="NewGarlic2!",
            new_recovery_key=manager.generate_recovery_key(),
        )

    assert path.read_bytes() == original
    assert store.authenticate(
        username="alice",
        password="Garlic1!",
    )
    assert store.unlock_dek_with_recovery(
        username="alice",
        recovery_key=old_key,
    ) == original_dek
    assert not list(tmp_path.glob(".account-credentials-*.tmp"))


def test_recovery_reset_preserves_private_permissions(tmp_path):

    path = tmp_path / "account-credentials.json"
    store = AccountCredentialStore(path=path)
    store.create(username="alice", password="Garlic1!")

    manager = AtRestKeyManager()
    old_key = manager.generate_recovery_key()

    store.enable_recovery(
        username="alice",
        password="Garlic1!",
        recovery_key=old_key,
    )

    store.reset_password_with_recovery(
        username="alice",
        recovery_key=old_key,
        new_password="NewGarlic2!",
        new_recovery_key=manager.generate_recovery_key(),
    )

    assert stat.S_IMODE(path.stat().st_mode) == 0o600


@pytest.mark.parametrize(
    "corrupted_value",
    [None, "not-hexadecimal", ""],
)
def test_corrupted_recovery_wrapping_fails_without_changes(
    tmp_path, corrupted_value,
):

    path = tmp_path / "account-credentials.json"
    store = AccountCredentialStore(path=path)
    store.create(username="alice", password="Garlic1!")

    recovery_key = AtRestKeyManager().generate_recovery_key()

    store.enable_recovery(
        username="alice",
        password="Garlic1!",
        recovery_key=recovery_key,
    )

    data = json.loads(path.read_text(encoding="utf-8"))
    data["wrapped_dek_recovery"] = corrupted_value
    path.write_text(json.dumps(data), encoding="utf-8")

    original = path.read_bytes()

    with pytest.raises(ValueError):
        store.unlock_dek_with_recovery(
            username="alice",
            recovery_key=recovery_key,
        )

    assert path.read_bytes() == original


def test_recovery_enable_fsync_failure_preserves_credentials(
    tmp_path, monkeypatch,
):

    path = tmp_path / "account-credentials.json"
    store = AccountCredentialStore(path=path)
    store.create(username="alice", password="Garlic1!")

    original = path.read_bytes()

    def fail_fsync(descriptor):
        raise OSError("Simulated fsync failure")

    monkeypatch.setattr(module.os, "fsync", fail_fsync)

    with pytest.raises(OSError, match="Simulated fsync failure"):
        store.enable_recovery(
            username="alice",
            password="Garlic1!",
            recovery_key=AtRestKeyManager().generate_recovery_key(),
        )

    assert path.read_bytes() == original
    assert store.authenticate(
        username="alice",
        password="Garlic1!",
    )
    assert not list(tmp_path.glob(".account-credentials-*.tmp"))


def test_replace_credentials_rejects_stale_snapshot(tmp_path):
    path = tmp_path / "account-credentials.json"
    store = AccountCredentialStore(path=path)
    store.create(username="alice", password="Garlic1!")

    first_snapshot = store._read_credentials()
    second_snapshot = store._read_credentials()

    first_update = first_snapshot.copy()
    first_update["revision_marker"] = "first"

    store._replace_credentials(
        first_update,
        expected_original=first_snapshot,
    )

    content_after_first_update = path.read_bytes()

    second_update = second_snapshot.copy()
    second_update["revision_marker"] = "second"

    with pytest.raises(
        ValueError,
        match="concurrent|stale|modified",
    ):
        store._replace_credentials(
            second_update,
            expected_original=second_snapshot,
        )

    assert path.read_bytes() == content_after_first_update


def test_replace_credentials_serializes_concurrent_updates(
    tmp_path,
    monkeypatch,
):
    import threading
    from concurrent.futures import ThreadPoolExecutor

    path = tmp_path / "account-credentials.json"
    store = AccountCredentialStore(path=path)
    store.create(username="alice", password="Garlic1!")

    original = store._read_credentials()

    first_update = original.copy()
    first_update["revision_marker"] = "first"

    second_update = original.copy()
    second_update["revision_marker"] = "second"

    barrier = threading.Barrier(2)

    def perform_update(data):
        barrier.wait(timeout=10)
        try:
            store._replace_credentials(
                data,
                expected_original=original,
            )
            return "updated"
        except ValueError as exc:
            if "modified concurrently" in str(exc):
                return "rejected"
            raise

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(perform_update, first_update)
        second = executor.submit(perform_update, second_update)

        results = [first.result(), second.result()]

    assert sorted(results) == ["rejected", "updated"]

    final_data = json.loads(path.read_text(encoding="utf-8"))
    assert final_data["revision_marker"] in {"first", "second"}


def _replace_credentials_in_process(
    path_string,
    expected_original,
    marker,
    start_event,
    result_queue,
):

    store = AccountCredentialStore(path=Path(path_string))
    updated = expected_original.copy()
    updated["revision_marker"] = marker

    if not start_event.wait(timeout=15):
        result_queue.put("timeout")
        return

    try:
        store._replace_credentials(
            updated,
            expected_original=expected_original,
        )
    except ValueError as exc:
        if "modified concurrently" in str(exc):
            result_queue.put("rejected")
        else:
            result_queue.put(f"unexpected: {exc}")
    except Exception as exc:
        result_queue.put(f"unexpected: {type(exc).__name__}: {exc}")
    else:
        result_queue.put("updated")


def _hold_credentials_lock(
    path_string,
    acquired_event,
    release_event,
    result_queue,
):
    from pathlib import Path
    from garlicsmtp.security.auth.account_credentials import (
        AccountCredentialStore,
    )

    store = AccountCredentialStore(Path(path_string))

    try:
        with store._credentials_write_lock():
            acquired_event.set()

            if not release_event.wait(timeout=15):
                result_queue.put("holder_timeout")
                return

        result_queue.put("holder_released")

    except Exception as exc:
        result_queue.put(
            f"holder_error: {type(exc).__name__}: {exc}"
        )


def _wait_for_credentials_lock(
    path_string,
    attempting_event,
    acquired_event,
    result_queue,
):

    store = AccountCredentialStore(Path(path_string))

    try:
        attempting_event.set()

        with store._credentials_write_lock():
            acquired_event.set()

        result_queue.put("waiter_acquired")

    except Exception as exc:
        result_queue.put(
            f"waiter_error: {type(exc).__name__}: {exc}"
        )


def test_replace_credentials_serializes_separate_processes(tmp_path):
    import multiprocessing

    path = tmp_path / "account-credentials.json"
    store = AccountCredentialStore(path=path)
    store.create(username="alice", password="Garlic1!")

    original = store._read_credentials()
    context = multiprocessing.get_context("spawn")

    start_event = context.Event()
    result_queue = context.Queue()

    processes = [
        context.Process(
            target=_replace_credentials_in_process,
            args=(
                str(path),
                original,
                marker,
                start_event,
                result_queue,
            ),
        )
        for marker in ("first", "second")
    ]

    try:
        for process in processes:
            process.start()

        start_event.set()

        results = [
            result_queue.get(timeout=20)
            for _ in processes
        ]

        for process in processes:
            process.join(timeout=10)

        assert all(
            process.exitcode == 0
            for process in processes
        )
        assert sorted(results) == ["rejected", "updated"]

        final_data = json.loads(path.read_text(encoding="utf-8"))
        assert final_data["revision_marker"] in {
            "first",
            "second",
        }
    finally:
        for process in processes:
            if process.is_alive():
                process.terminate()
            process.join(timeout=5)

        result_queue.close()
        result_queue.join_thread()


def test_credentials_lock_file_has_private_permissions(tmp_path):
    import stat

    path = tmp_path / "account-credentials.json"
    store = AccountCredentialStore(path=path)
    store.create(username="alice", password="Garlic1!")

    original = store._read_credentials()
    updated = original.copy()
    updated["revision_marker"] = "updated"

    store._replace_credentials(
        updated,
        expected_original=original,
    )

    lock_path = path.with_name(path.name + ".lock")

    assert lock_path.is_file()
    assert stat.S_IMODE(lock_path.stat().st_mode) == 0o600


def test_credentials_rejects_insecure_lock_permissions(tmp_path):
    path = tmp_path / "account-credentials.json"
    store = AccountCredentialStore(path=path)
    store.create(username="alice", password="Garlic1!")

    original = store._read_credentials()

    lock_path = path.with_name(path.name + ".lock")
    lock_path.write_text("", encoding="utf-8")
    lock_path.chmod(0o644)

    updated = original.copy()
    updated["revision_marker"] = "updated"

    with pytest.raises(
        PermissionError,
        match="Insecure credentials lock permissions",
    ):
        store._replace_credentials(
            updated,
            expected_original=original,
        )

    assert store._read_credentials() == original


def test_credentials_rejects_non_regular_lock_file(tmp_path):
    path = tmp_path / "account-credentials.json"
    store = AccountCredentialStore(path=path)
    store.create(username="alice", password="Garlic1!")

    original = store._read_credentials()

    lock_path = path.with_name(path.name + ".lock")
    lock_path.mkdir()
    lock_path.chmod(0o600)

    updated = original.copy()
    updated["revision_marker"] = "updated"

    with pytest.raises(
        (ValueError, PermissionError),
        match="Invalid credentials lock|Insecure credentials lock",
    ):
        store._replace_credentials(
            updated,
            expected_original=original,
        )

    assert store._read_credentials() == original


def test_credentials_rejects_fifo_lock_file(tmp_path):
    import os

    path = tmp_path / "account-credentials.json"
    store = AccountCredentialStore(path=path)
    store.create(username="alice", password="Garlic1!")

    original = store._read_credentials()

    lock_path = path.with_name(path.name + ".lock")
    os.mkfifo(lock_path, 0o600)

    updated = original.copy()
    updated["revision_marker"] = "updated"

    with pytest.raises(
        ValueError,
        match="Invalid credentials lock",
    ):
        store._replace_credentials(
            updated,
            expected_original=original,
        )

    assert store._read_credentials() == original


def test_credentials_lock_blocks_second_process_until_release(
    tmp_path,
):
    import multiprocessing

    path = tmp_path / "account-credentials.json"
    store = AccountCredentialStore(path=path)
    store.create(username="alice", password="Garlic1!")

    context = multiprocessing.get_context("spawn")

    holder_acquired = context.Event()
    holder_release = context.Event()
    waiter_attempting = context.Event()
    waiter_acquired = context.Event()
    result_queue = context.Queue()

    holder = context.Process(
        target=_hold_credentials_lock,
        args=(
            str(path),
            holder_acquired,
            holder_release,
            result_queue,
        ),
    )

    waiter = context.Process(
        target=_wait_for_credentials_lock,
        args=(
            str(path),
            waiter_attempting,
            waiter_acquired,
            result_queue,
        ),
    )

    try:
        holder.start()

        assert holder_acquired.wait(timeout=10), (
            "First process did not acquire the lock"
        )

        waiter.start()

        assert waiter_attempting.wait(timeout=10), (
            "Second process did not attempt the lock"
        )

        # Il primo processo detiene ancora il lock.
        # Il secondo non deve poterlo acquisire.
        assert not waiter_acquired.wait(timeout=0.5), (
            "Second process acquired a lock still held "
            "by the first process"
        )

        holder_release.set()

        assert waiter_acquired.wait(timeout=10), (
            "Second process did not acquire the lock "
            "after release"
        )

        holder.join(timeout=10)
        waiter.join(timeout=10)

        assert holder.exitcode == 0
        assert waiter.exitcode == 0

        results = {
            result_queue.get(timeout=5),
            result_queue.get(timeout=5),
        }

        assert results == {
            "holder_released",
            "waiter_acquired",
        }

    finally:
        holder_release.set()

        for process in (holder, waiter):
            if process.is_alive():
                process.terminate()
            process.join(timeout=5)

        result_queue.close()
        result_queue.join_thread()


def test_enable_recovery_starts_unconfirmed(
    tmp_path,
):
    path = tmp_path / "account-credentials.json"

    store = AccountCredentialStore(path=path)

    store.create(
        username="alice",
        password="Garlic1!",
    )

    recovery_key = (
        AtRestKeyManager().generate_recovery_key()
    )

    store.enable_recovery(
        username="alice",
        password="Garlic1!",
        recovery_key=recovery_key,
    )

    data = json.loads(
        path.read_text(encoding="utf-8")
    )

    assert data["recovery_confirmed"] is False

    assert store.unlock_dek_with_password(
        username="alice",
        password="Garlic1!",
    ) == store.unlock_dek_with_recovery(
        username="alice",
        recovery_key=recovery_key,
    )



def test_confirm_recovery_preserves_credentials_and_dek(
    tmp_path,
):
    path = tmp_path / "account-credentials.json"
    store = AccountCredentialStore(path=path)

    store.create(
        username="alice",
        password="Garlic1!",
    )

    recovery_key = AtRestKeyManager().generate_recovery_key()
    store.enable_recovery(
        username="alice",
        password="Garlic1!",
        recovery_key=recovery_key,
    )

    before = json.loads(path.read_text(encoding="utf-8"))
    assert before["recovery_confirmed"] is False

    store.confirm_recovery(username="alice", recovery_key=recovery_key)

    after = json.loads(path.read_text(encoding="utf-8"))

    assert after["recovery_confirmed"] is True
    assert after["password_hash"] == before["password_hash"]
    assert (
        after["wrapped_dek_password"]
        == before["wrapped_dek_password"]
    )
    assert (
        after["wrapped_dek_recovery"]
        == before["wrapped_dek_recovery"]
    )
    assert store.unlock_dek_with_password(
        username="alice",
        password="Garlic1!",
    ) == store.unlock_dek_with_recovery(
        username="alice",
        recovery_key=recovery_key,
    )


def test_replace_unconfirmed_recovery_preserves_dek(tmp_path):
    store = AccountCredentialStore(
        path=tmp_path / "account.json",
    )

    store.create(
        username="alice",
        password="Garlic1!",
    )

    store.enable_recovery(
        username="alice",
        password="Garlic1!",
        recovery_key="old-recovery-key",
    )

    original_dek = store.unlock_dek_with_password(
        username="alice",
        password="Garlic1!",
    )

    store.replace_unconfirmed_recovery(
        username="alice",
        password="Garlic1!",
        new_recovery_key="new-recovery-key",
    )

    assert store.unlock_dek_with_password(
        username="alice",
        password="Garlic1!",
    ) == original_dek

    assert store.unlock_dek_with_recovery(
        username="alice",
        recovery_key="new-recovery-key",
    ) == original_dek

    with pytest.raises(ValueError, match="Invalid wrapped DEK"):
        store.unlock_dek_with_recovery(
            username="alice",
            recovery_key="old-recovery-key",
        )

    credentials = store._read_credentials()

    assert credentials["recovery_confirmed"] is False


def test_replace_unconfirmed_recovery_rejects_wrong_password(tmp_path):
    store = AccountCredentialStore(
        path=tmp_path / "account.json",
    )

    store.create(
        username="alice",
        password="Garlic1!",
    )

    store.enable_recovery(
        username="alice",
        password="Garlic1!",
        recovery_key="original-recovery-key",
    )

    original_credentials = store._read_credentials()

    with pytest.raises(ValueError, match="Invalid account credentials"):
        store.replace_unconfirmed_recovery(
            username="alice",
            password="Wrong1!",
            new_recovery_key="replacement-recovery-key",
        )

    assert store._read_credentials() == original_credentials

    assert len(
        store.unlock_dek_with_recovery(
            username="alice",
            recovery_key="original-recovery-key",
        )
    ) == 32


def test_replace_unconfirmed_recovery_rejects_confirmed_account(tmp_path):
    store = AccountCredentialStore(
        path=tmp_path / "account.json",
    )

    store.create(
        username="alice",
        password="Garlic1!",
    )

    store.enable_recovery(
        username="alice",
        password="Garlic1!",
        recovery_key="original-recovery-key",
    )

    store.confirm_recovery(username="alice", recovery_key="original-recovery-key")

    original_credentials = store._read_credentials()
    original_dek = store.unlock_dek_with_password(
        username="alice",
        password="Garlic1!",
    )

    with pytest.raises(ValueError, match="Recovery setup is not pending"):
        store.replace_unconfirmed_recovery(
            username="alice",
            password="Garlic1!",
            new_recovery_key="replacement-recovery-key",
        )

    assert store._read_credentials() == original_credentials

    assert store.unlock_dek_with_recovery(
        username="alice",
        recovery_key="original-recovery-key",
    ) == original_dek


def test_confirm_recovery_directory_fsync_failure_keeps_new_state(
    tmp_path,
    monkeypatch,
):
    path = tmp_path / "account-credentials.json"
    store = AccountCredentialStore(path=path)

    store.create(
        username="alice",
        password="Garlic1!",
    )
    store.enable_recovery(
        username="alice",
        password="Garlic1!",
        recovery_key="test-recovery-key",
    )

    original_dek = store.unlock_dek_with_password(
        username="alice",
        password="Garlic1!",
    )

    original_fsync = module.os.fsync

    def fail_directory_fsync(descriptor):
        if stat.S_ISDIR(os.fstat(descriptor).st_mode):
            raise OSError("Simulated directory fsync failure")
        return original_fsync(descriptor)

    monkeypatch.setattr(
        module.os,
        "fsync",
        fail_directory_fsync,
    )

    with pytest.raises(
        OSError,
        match="Simulated directory fsync failure",
    ):
        store.confirm_recovery(username="alice", recovery_key="test-recovery-key")

    credentials = store._read_credentials()

    assert credentials["recovery_confirmed"] is True

    assert store.unlock_dek_with_password(
        username="alice",
        password="Garlic1!",
    ) == original_dek

    assert store.unlock_dek_with_recovery(
        username="alice",
        recovery_key="test-recovery-key",
    ) == original_dek


def test_wrong_recovery_key_raises_value_error(tmp_path):
    from garlicsmtp.security.auth.account_credentials import (
        AccountCredentialStore,
    )
    from garlicsmtp.security.at_rest_key_manager import (
        AtRestKeyManager,
    )

    store = AccountCredentialStore(
        path=tmp_path / "credentials.json",
    )

    username = "developer_test"
    password = "DeveloperTest-Password-2026!"

    manager = AtRestKeyManager()
    recovery_key = manager.generate_recovery_key()

    store.create(
        username=username,
        password=password,
    )
    store.enable_recovery(
        username=username,
        password=password,
        recovery_key=recovery_key,
    )
    store.confirm_recovery(username=username, recovery_key=recovery_key)

    with pytest.raises(ValueError, match="Invalid wrapped DEK"):
        store.unlock_dek_with_recovery(
            username=username,
            recovery_key=manager.generate_recovery_key(),
        )

def test_confirm_recovery_rejects_wrong_key(tmp_path):
    path = tmp_path / "account-credentials.json"
    store = AccountCredentialStore(path=path)

    store.create(
        username="alice",
        password="Garlic1!",
    )

    recovery_key = AtRestKeyManager().generate_recovery_key()

    store.enable_recovery(
        username="alice",
        password="Garlic1!",
        recovery_key=recovery_key,
    )

    with pytest.raises(ValueError):
        store.confirm_recovery(
            username="alice",
            recovery_key="wrong-recovery-key",
        )

    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["recovery_confirmed"] is False
