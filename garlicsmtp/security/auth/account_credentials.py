# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import json
from pathlib import Path
import stat
import os
import tempfile
import fcntl
import threading
from contextlib import contextmanager

from garlicsmtp.security.at_rest_key_manager import AtRestKeyManager
from garlicsmtp.security.auth.password_hasher import (
    PasswordHasher,
)
from cryptography.exceptions import InvalidTag

_CREDENTIAL_LOCKS_GUARD = threading.Lock()
_CREDENTIAL_LOCKS = {}


def _thread_lock_for(path: Path) -> threading.Lock:
    key = str(path.absolute())

    with _CREDENTIAL_LOCKS_GUARD:
        if key not in _CREDENTIAL_LOCKS:
            _CREDENTIAL_LOCKS[key] = threading.Lock()

        return _CREDENTIAL_LOCKS[key]


class AccountCredentialStore:

    def __init__(
        self,
        path: Path,
    ):
        self.path = path

    def create(
        self,
        *,
        username: str,
        password: str,
    ) -> None:
        if not username.strip():
            raise ValueError(
                "Account username is required"
            )

        self._validate_password_policy(password)

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        data = {
            "username": username,
            "password_hash": (
                PasswordHasher().hash_password(
                    password
                )
            ),
        }

        file_descriptor = os.open(
            self.path,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
        )

        with os.fdopen(
            file_descriptor,
            "w",
            encoding="utf-8",
        ) as credentials_file:
            credentials_file.write(
                json.dumps(data)
            )

    def validate(
        self,
    ) -> None:

        file_stat = self.path.lstat()

        if stat.S_ISLNK(
            file_stat.st_mode
        ):
            raise ValueError(
                "Invalid account credentials"
            )

        mode = stat.S_IMODE(
            file_stat.st_mode
        )

        if mode != 0o600:
            raise PermissionError(
                "Insecure account credentials permissions"
            )

        try:
            data = json.loads(
                self.path.read_text(
                    encoding="utf-8",
                )
            )
        except json.JSONDecodeError as exc:
            raise ValueError(
                "Invalid account credentials"
            ) from exc

        if (
            "username" not in data
            or "password_hash" not in data
        ):
            raise ValueError(
                "Invalid account credentials"
            )

        password_hash = data["password_hash"]

        if (
            not isinstance(
                password_hash,
                str,
            )
            or len(
                password_hash.split("$")
            ) != 7
            or not password_hash.startswith(
                "scrypt$"
            )
        ):
            raise ValueError(
                "Invalid account credentials"
            )

    def authenticate(
        self,
        *,
        username: str,
        password: str,
    ) -> bool:
        self.validate()
        data = json.loads(
            self.path.read_text(
                encoding="utf-8",
            )
        )

        if data["username"] != username:
            return False

        return PasswordHasher().verify_password(
            password,
            data["password_hash"],
        )

    def enable_recovery(
        self,
        *,
        username: str,
        password: str,
        recovery_key: str,
    ) -> None:
        if not self.authenticate(
            username=username,
            password=password,
        ):
            raise ValueError("Invalid account credentials")

        if not isinstance(recovery_key, str) or not recovery_key:
            raise ValueError("Recovery key is required")

        data = self._read_credentials()

        original = data.copy()

        if (
            "wrapped_dek_password" in data
            or "wrapped_dek_recovery" in data
        ):
            raise ValueError("Recovery already enabled")

        manager = AtRestKeyManager()
        dek = manager.generate_dek()

        data["wrapped_dek_password"] = manager.wrap_dek(
            dek=dek,
            secret=password,
            purpose="password",
        ).hex()

        data["wrapped_dek_recovery"] = manager.wrap_dek(
            dek=dek,
            secret=recovery_key,
            purpose="recovery",
        ).hex()

        data["recovery_confirmed"] = False

        self._replace_credentials(
            data,
            expected_original=original,
        )

    def replace_unconfirmed_recovery(
        self,
        *,
        username: str,
        password: str,
        new_recovery_key: str,
    ) -> None:
        if not self.authenticate(
            username=username,
            password=password,
        ):
            raise ValueError("Invalid account credentials")

        if not isinstance(new_recovery_key, str) or not new_recovery_key:
            raise ValueError("Recovery key is required")

        data = self._read_credentials()
        original = data.copy()

        if data.get("recovery_confirmed") is not False:
            raise ValueError("Recovery setup is not pending")

        if not isinstance(data.get("wrapped_dek_recovery"), str):
            raise ValueError("Recovery is not enabled")

        dek = self._unwrap_stored_dek(
            data=data,
            field="wrapped_dek_password",
            secret=password,
            purpose="password",
        )

        data["wrapped_dek_recovery"] = AtRestKeyManager().wrap_dek(
            dek=dek,
            secret=new_recovery_key,
            purpose="recovery",
        ).hex()

        self._replace_credentials(
            data,
            expected_original=original,
        )


    def confirm_recovery(
        self,
        *,
        username: str,
        recovery_key: str,
    ) -> None:
        data = self._read_credentials()
        original = data.copy()

        if data["username"] != username:
            raise ValueError("Invalid account credentials")

        if (
            not isinstance(data.get("wrapped_dek_password"), str)
            or not isinstance(data.get("wrapped_dek_recovery"), str)
        ):
            raise ValueError("Recovery is not enabled")

        self._unwrap_stored_dek(
            data=data,
            field="wrapped_dek_recovery",
            secret=recovery_key,
            purpose="recovery",
        )

        if data.get("recovery_confirmed") is True:
            return

        data["recovery_confirmed"] = True

        self._replace_credentials(
            data,
            expected_original=original,
        )


    def unlock_dek_with_password(
        self,
        *,
        username: str,
        password: str,
    ) -> bytes:
        if not self.authenticate(
            username=username,
            password=password,
        ):
            raise ValueError("Invalid account credentials")

        data = self._read_credentials()

        return self._unwrap_stored_dek(
            data=data,
            field="wrapped_dek_password",
            secret=password,
            purpose="password",
        )

    def unlock_dek_with_recovery(
        self,
        *,
        username: str,
        recovery_key: str,
    ) -> bytes:
        data = self._read_credentials()

        if data["username"] != username:
            raise ValueError("Invalid account credentials")

        return self._unwrap_stored_dek(
            data=data,
            field="wrapped_dek_recovery",
            secret=recovery_key,
            purpose="recovery",
        )

    def reset_password_with_recovery(
        self,
        *,
        username: str,
        recovery_key: str,
        new_password: str,
        new_recovery_key: str,
    ) -> None:
        data = self._read_credentials()

        original = data.copy()

        if data["username"] != username:
            raise ValueError("Invalid account credentials")

        # La recovery corrente deve sbloccare la DEK prima
        # di qualsiasi modifica alle credenziali.
        dek = self._unwrap_stored_dek(
            data=data,
            field="wrapped_dek_recovery",
            secret=recovery_key,
            purpose="recovery",
        )

        self._validate_password_policy(new_password)

        if (
            not isinstance(new_recovery_key, str)
            or not new_recovery_key
            or new_recovery_key == recovery_key
        ):
            raise ValueError("A new recovery key is required")

        manager = AtRestKeyManager()

        # Conserviamo la stessa DEK: i dati già cifrati
        # devono restare accessibili.
        data["password_hash"] = PasswordHasher().hash_password(
            new_password
        )

        data["wrapped_dek_password"] = manager.wrap_dek(
            dek=dek,
            secret=new_password,
            purpose="password",
        ).hex()

        data["wrapped_dek_recovery"] = manager.wrap_dek(
            dek=dek,
            secret=new_recovery_key,
            purpose="recovery",
        ).hex()

        self._replace_credentials(
            data,
            expected_original=original,
        )

    @staticmethod
    def _validate_password_policy(password: str) -> None:
        if len(password) < 8:
            raise ValueError(
                "Account password must be at least 8 characters"
            )

        if not any(character.isupper() for character in password):
            raise ValueError(
                "Account password must contain an uppercase letter"
            )

        if not any(character.isdigit() for character in password):
            raise ValueError(
                "Account password must contain a digit"
            )

        if not any(
            not character.isalnum()
            for character in password
        ):
            raise ValueError(
                "Account password must contain a special character"
            )

    def _read_credentials(self) -> dict:
        self.validate()
        return json.loads(
            self.path.read_text(encoding="utf-8")
        )

    @staticmethod
    def _unwrap_stored_dek(
        *,
        data: dict,
        field: str,
        secret: str,
        purpose: str,
    ) -> bytes:
        wrapped_hex = data.get(field)

        if not isinstance(wrapped_hex, str):
            raise ValueError("Recovery is not enabled")

        try:
            wrapped = bytes.fromhex(wrapped_hex)
        except ValueError as exc:
            raise ValueError(
                "Invalid wrapped DEK"
            ) from exc

        try:
            return AtRestKeyManager().unwrap_dek(
                wrapped=wrapped,
                secret=secret,
                purpose=purpose,
            )
        except InvalidTag as exc:
            raise ValueError(
                "Invalid wrapped DEK"
            ) from exc

    def _replace_credentials(
        self,
        data: dict,
        *,
        expected_original: dict,
    ) -> None:
        with self._credentials_write_lock():
            self.validate()

            current = self._read_credentials()

            if current != expected_original:
                raise ValueError(
                    "Credentials modified concurrently"
                )

            temporary_path = None

            try:
                descriptor, name = tempfile.mkstemp(
                    prefix=".account-credentials-",
                    suffix=".tmp",
                    dir=self.path.parent,
                )
                temporary_path = Path(name)

                with os.fdopen(
                    descriptor,
                    "w",
                    encoding="utf-8",
                ) as credentials_file:
                    credentials_file.write(json.dumps(data))
                    credentials_file.flush()
                    os.fsync(credentials_file.fileno())

                os.chmod(temporary_path, 0o600)
                os.replace(temporary_path, self.path)
                temporary_path = None

                directory_descriptor = os.open(
                    self.path.parent,
                    os.O_RDONLY | getattr(
                        os,
                        "O_DIRECTORY",
                        0,
                    ),
                )
                try:
                    os.fsync(directory_descriptor)
                finally:
                    os.close(directory_descriptor)

            finally:
                if temporary_path is not None:
                    temporary_path.unlink(
                        missing_ok=True
                    )

    @contextmanager
    def _credentials_write_lock(self):
        lock_path = self.path.with_name(
            self.path.name + ".lock"
        )

        thread_lock = _thread_lock_for(lock_path)

        with thread_lock:
            try:
                descriptor = os.open(
                    lock_path,
                    os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW,
                    0o600,
                )
            except IsADirectoryError as exc:
                raise ValueError(
                    "Invalid credentials lock"
                ) from exc

            try:
                file_stat = os.fstat(descriptor)

                if not stat.S_ISREG(file_stat.st_mode):
                    raise ValueError(
                        "Invalid credentials lock"
                    )

                mode = stat.S_IMODE(file_stat.st_mode)

                if mode != 0o600:
                    raise PermissionError(
                        "Insecure credentials lock permissions"
                    )

                fcntl.flock(
                    descriptor,
                    fcntl.LOCK_EX,
                )

                try:
                    yield
                finally:
                    fcntl.flock(
                        descriptor,
                        fcntl.LOCK_UN,
                    )
            finally:
                os.close(descriptor)