# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import os
import tempfile
from pathlib import Path


class OnionServiceManager:

    def __init__(
        self,
        *,
        client,
        authenticator=None,
        identity_file: Path,
        virtual_port: int,
        target_host: str,
        target_port: int,
        hostname_callback=None,
    ) -> None:
        self.client = client
        self.authenticator = authenticator
        self.identity_file = identity_file
        self.virtual_port = virtual_port
        self.target_host = target_host
        self.target_port = target_port
        self.hostname_callback = (
            hostname_callback
        )

        self.hostname: str | None = None

    def start(
        self,
    ) -> None:
        self.client.connect()

        if self.authenticator is not None:
            self.authenticator.authenticate()

        self.hostname = self.ensure_service()

        if self.hostname_callback is not None:
            self.hostname_callback(
                self.hostname
            )

    def stop(
        self,
    ) -> None:
        self.client.close()

    def ensure_service(
        self,
    ) -> str:
        self._prepare_identity_directory()

        if self.identity_file.is_symlink():
            raise RuntimeError(
                "Onion Service identity file "
                "must not be a symlink"
            )

        if self.identity_file.exists():
            self._protect_identity_file()

            key = self.identity_file.read_text(
                encoding="utf-8"
            ).strip()

            if not key:
                raise RuntimeError(
                    "Onion Service identity file "
                    "is empty"
                )
        else:
            key = "NEW:ED25519-V3"

        service = self.client.add_onion(
            key=key,
            virtual_port=self.virtual_port,
            target_host=self.target_host,
            target_port=self.target_port,
        )

        if key == "NEW:ED25519-V3":
            self._write_identity_atomically(
                service.private_key
            )

        return (
            service.service_id
            + ".onion"
        )

    def _prepare_identity_directory(
        self,
    ) -> None:
        directory = self.identity_file.parent

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        if os.name != "nt":
            directory.chmod(
                0o700
            )

    def _protect_identity_file(
        self,
    ) -> None:
        if os.name != "nt":
            self.identity_file.chmod(
                0o600
            )

    def _write_identity_atomically(
        self,
        private_key: str,
    ) -> None:
        directory = self.identity_file.parent
        temporary_path = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=directory,
                prefix=(
                    "."
                    + self.identity_file.name
                    + "."
                ),
                delete=False,
            ) as temporary_file:
                temporary_path = Path(
                    temporary_file.name
                )

                if os.name != "nt":
                    temporary_path.chmod(
                        0o600
                    )

                temporary_file.write(
                    private_key
                )

                temporary_file.flush()

                os.fsync(
                    temporary_file.fileno()
                )

            os.replace(
                temporary_path,
                self.identity_file,
            )

            self._protect_identity_file()

        finally:
            if (
                temporary_path is not None
                and temporary_path.exists()
            ):
                temporary_path.unlink()