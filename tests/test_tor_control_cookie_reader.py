import os
from pathlib import Path

import pytest

from garlicsmtp.tor.control import (
    SafeCookieReader,
    TorControlSecurityError,
)


def create_cookie(
    path: Path,
    content: bytes = b"C" * 32,
    mode: int = 0o600,
) -> None:
    path.write_bytes(
        content
    )

    path.chmod(
        mode
    )


def test_cookie_reader_reads_secure_cookie(
    tmp_path,
):
    path = (
        tmp_path
        / "control.authcookie"
    )

    create_cookie(
        path
    )

    cookie = SafeCookieReader().read(
        path
    )

    assert cookie == b"C" * 32
    assert isinstance(
        cookie,
        bytes,
    )


def test_cookie_reader_allows_group_read(
    tmp_path,
):
    path = (
        tmp_path
        / "control.authcookie"
    )

    create_cookie(
        path,
        mode=0o640,
    )

    assert SafeCookieReader().read(
        path
    ) == b"C" * 32


def test_cookie_reader_rejects_relative_path():
    with pytest.raises(
        TorControlSecurityError
    ):
        SafeCookieReader().read(
            Path(
                "control.authcookie"
            )
        )



@pytest.mark.parametrize(
    "content",
    [
        b"",
        b"C" * 31,
        b"C" * 33,
    ],
)
def test_cookie_reader_rejects_invalid_size(
    tmp_path,
    content,
):
    path = (
        tmp_path
        / "control.authcookie"
    )

    create_cookie(
        path,
        content=content,
    )

    with pytest.raises(
        TorControlSecurityError
    ):
        SafeCookieReader().read(
            path
        )



def test_cookie_reader_rejects_symlink(
    tmp_path,
):
    target = (
        tmp_path
        / "real.cookie"
    )

    link = (
        tmp_path
        / "control.authcookie"
    )

    create_cookie(
        target
    )

    link.symlink_to(
        target
    )

    with pytest.raises(
        TorControlSecurityError
    ):
        SafeCookieReader().read(
            link
        )



def test_cookie_reader_rejects_directory(
    tmp_path,
):
    directory = (
        tmp_path
        / "cookie-directory"
    )

    directory.mkdir()

    with pytest.raises(
        TorControlSecurityError
    ):
        SafeCookieReader().read(
            directory
        )



@pytest.mark.skipif(
    not hasattr(
        os,
        "mkfifo",
    ),
    reason="FIFO unsupported",
)
def test_cookie_reader_rejects_fifo(
    tmp_path,
):
    path = (
        tmp_path
        / "cookie-fifo"
    )

    os.mkfifo(
        path,
        0o600,
    )

    # Non chiamiamo read() direttamente:
    # l'apertura read-only di una FIFO può
    # bloccarsi in attesa di uno scrittore.
    #
    # Verifichiamo la validazione metadata
    # tramite un descrittore non bloccante.
    descriptor = os.open(
        path,
        os.O_RDONLY
        | os.O_NONBLOCK,
    )

    try:
        metadata = os.fstat(
            descriptor
        )

        with pytest.raises(
            TorControlSecurityError
        ):
            SafeCookieReader._validate_metadata(
                metadata
            )
    finally:
        os.close(
            descriptor
        )



@pytest.mark.parametrize(
    "mode",
    [
        0o620,
        0o602,
        0o666,
    ],
)
def test_cookie_reader_rejects_writable_by_others(
    tmp_path,
    mode,
):
    path = (
        tmp_path
        / "control.authcookie"
    )

    create_cookie(
        path,
        mode=mode,
    )

    with pytest.raises(
        TorControlSecurityError
    ):
        SafeCookieReader().read(
            path
        )



@pytest.mark.parametrize(
    "mode",
    [
        0o604,
        0o644,
    ],
)
def test_cookie_reader_rejects_world_readable(
    tmp_path,
    mode,
):
    path = (
        tmp_path
        / "control.authcookie"
    )

    create_cookie(
        path,
        mode=mode,
    )

    with pytest.raises(
        TorControlSecurityError
    ):
        SafeCookieReader().read(
            path
        )



def test_cookie_reader_rejects_missing_file(
    tmp_path,
):
    path = (
        tmp_path
        / "missing.authcookie"
    )

    with pytest.raises(
        TorControlSecurityError
    ):
        SafeCookieReader().read(
            path
        )



def test_cookie_reader_requires_path():
    with pytest.raises(
        TypeError
    ):
        SafeCookieReader().read(
            "/run/tor/control.authcookie"
        )



def test_cookie_reader_preserves_binary_data(
    tmp_path,
):
    path = (
        tmp_path
        / "control.authcookie"
    )

    content = bytes(
        range(32)
    )

    create_cookie(
        path,
        content=content,
    )

    assert SafeCookieReader().read(
        path
    ) == content



def test_cookie_reader_detects_metadata_change(
    tmp_path,
):
    first = (
        tmp_path
        / "first.cookie"
    )

    second = (
        tmp_path
        / "second.cookie"
    )

    create_cookie(
        first
    )

    create_cookie(
        second
    )

    first_metadata = (
        first.stat()
    )

    second_metadata = (
        second.stat()
    )

    with pytest.raises(
        TorControlSecurityError
    ):
        SafeCookieReader._validate_unchanged(
            first_metadata,
            second_metadata,
        )




