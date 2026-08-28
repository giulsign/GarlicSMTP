# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import os
import stat
from pathlib import Path

from garlicsmtp.tor.control.exceptions import (
    TorControlSecurityError,
)
from garlicsmtp.tor.control.safecookie import (
    SAFECOOKIE_VALUE_BYTES,
)


class SafeCookieReader:

    def read(
        self,
        path: Path,
    ) -> bytes:
        normalized_path = self._validate_path(
            path
        )

        descriptor = self._open_securely(
            normalized_path
        )

        try:
            before = os.fstat(
                descriptor
            )

            self._validate_metadata(
                before
            )

            cookie = self._read_exactly(
                descriptor,
                SAFECOOKIE_VALUE_BYTES,
            )

            extra = os.read(
                descriptor,
                1,
            )

            if extra:
                raise TorControlSecurityError(
                    "Tor authentication cookie "
                    "contains unexpected data"
                )

            after = os.fstat(
                descriptor
            )

            self._validate_unchanged(
                before,
                after,
            )

            return cookie

        finally:
            try:
                os.close(
                    descriptor
                )
            except OSError:
                pass

    @staticmethod
    def _validate_path(
        path: Path,
    ) -> Path:
        if not isinstance(
            path,
            Path,
        ):
            raise TypeError(
                "cookie path must be a Path"
            )

        if not path.is_absolute():
            raise TorControlSecurityError(
                "Tor authentication cookie "
                "path must be absolute"
            )

        return path

    @staticmethod
    def _open_securely(
        path: Path,
    ) -> int:
        flags = (
            os.O_RDONLY
            | getattr(
                os,
                "O_CLOEXEC",
                0,
            )
        )

        no_follow = getattr(
            os,
            "O_NOFOLLOW",
            None,
        )

        if no_follow is None:
            raise TorControlSecurityError(
                "Secure cookie reading requires "
                "O_NOFOLLOW support"
            )

        flags |= no_follow

        try:
            return os.open(
                path,
                flags,
            )

        except OSError as exc:
            raise TorControlSecurityError(
                "Unable to securely open the "
                "Tor authentication cookie"
            ) from exc

    @staticmethod
    def _validate_metadata(
        metadata: os.stat_result,
    ) -> None:
        if not stat.S_ISREG(
            metadata.st_mode
        ):
            raise TorControlSecurityError(
                "Tor authentication cookie "
                "must be a regular file"
            )

        if (
            metadata.st_size
            != SAFECOOKIE_VALUE_BYTES
        ):
            raise TorControlSecurityError(
                "Tor authentication cookie "
                "must be exactly 32 bytes"
            )

        unsafe_write_bits = (
            stat.S_IWGRP
            | stat.S_IWOTH
        )

        if (
            metadata.st_mode
            & unsafe_write_bits
        ):
            raise TorControlSecurityError(
                "Tor authentication cookie "
                "must not be writable by "
                "group or others"
            )

        if (
            metadata.st_mode
            & stat.S_IROTH
        ):
            raise TorControlSecurityError(
                "Tor authentication cookie "
                "must not be readable by others"
            )

    @staticmethod
    def _read_exactly(
        descriptor: int,
        length: int,
    ) -> bytes:
        chunks = bytearray()

        while len(chunks) < length:
            try:
                chunk = os.read(
                    descriptor,
                    length - len(chunks),
                )

            except OSError as exc:
                raise TorControlSecurityError(
                    "Unable to read the Tor "
                    "authentication cookie"
                ) from exc

            if not chunk:
                raise TorControlSecurityError(
                    "Tor authentication cookie "
                    "ended unexpectedly"
                )

            chunks.extend(
                chunk
            )

        return bytes(
            chunks
        )

    @staticmethod
    def _validate_unchanged(
        before: os.stat_result,
        after: os.stat_result,
    ) -> None:
        stable_fields = (
            "st_dev",
            "st_ino",
            "st_mode",
            "st_uid",
            "st_gid",
            "st_size",
        )

        for field in stable_fields:
            if (
                getattr(before, field)
                != getattr(after, field)
            ):
                raise TorControlSecurityError(
                    "Tor authentication cookie "
                    "changed while being read"
                )

        before_mtime_ns = getattr(
            before,
            "st_mtime_ns",
            None,
        )

        after_mtime_ns = getattr(
            after,
            "st_mtime_ns",
            None,
        )

        if (
            before_mtime_ns is not None
            and after_mtime_ns is not None
            and before_mtime_ns
            != after_mtime_ns
        ):
            raise TorControlSecurityError(
                "Tor authentication cookie "
                "changed while being read"
            )
