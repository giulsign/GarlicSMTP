# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import pytest
from install.platform import is_supported_platform, parse_os_release, select_platform_profile, detect_platform_profile, read_os_release


def test_parse_os_release_extracts_linux_distribution_identity():
    os_release = """
PRETTY_NAME="Ubuntu 24.04.4 LTS"
NAME="Ubuntu"
VERSION_ID="24.04"
VERSION_CODENAME=noble
ID=ubuntu
ID_LIKE=debian
""".strip()

    assert parse_os_release(os_release) == {
        "id": "ubuntu",
        "id_like": ("debian",),
        "version_id": "24.04",
        "version_codename": "noble",
    }


def test_ubuntu_24_04_is_supported_installation_platform():
    platform = {
        "id": "ubuntu",
        "id_like": ("debian",),
        "version_id": "24.04",
        "version_codename": "noble",
    }
    supported_profiles = [
        {
            "id": "ubuntu",
            "version_id": "24.04",
        },
    ]

    assert is_supported_platform(platform, supported_profiles) is True


def test_debian_is_not_implicitly_supported_through_id_like():
    platform = {
        "id": "debian",
        "id_like": (),
        "version_id": "12",
        "version_codename": "bookworm",
    }
    supported_profiles = [
        {
            "id": "ubuntu",
            "version_id": "24.04",
        },
    ]

    assert is_supported_platform(platform, supported_profiles) is False


def test_platform_is_not_supported_when_no_profile_is_declared():
    platform = {
        "id": "ubuntu",
        "id_like": ("debian",),
        "version_id": "24.04",
        "version_codename": "noble",
    }

    assert is_supported_platform(platform, []) is False


def test_real_manifest_profile_supports_ubuntu_24_04():
    from pathlib import Path
    import tomllib

    project_root = Path(__file__).resolve().parents[1]

    with (project_root / "install" / "manifest.toml").open("rb") as manifest_file:
        manifest = tomllib.load(manifest_file)

    platform = parse_os_release(
        """
ID=ubuntu
ID_LIKE=debian
VERSION_ID="24.04"
VERSION_CODENAME=noble
""".strip()
    )

    assert is_supported_platform(
        platform,
        manifest["platform"]["profiles"],
    ) is True


def test_select_platform_profile_returns_exact_matching_profile():
    platform = {
        "id": "ubuntu",
        "id_like": ("debian",),
        "version_id": "24.04",
        "version_codename": "noble",
    }

    supported_profiles = [
        {
            "id": "ubuntu",
            "version_id": "24.04",
            "package_manager": "apt-get",
        },
    ]

    profile = select_platform_profile(
        platform,
        supported_profiles,
    )

    assert profile == supported_profiles[0]


def test_select_platform_profile_rejects_id_like_match():
    platform = {
        "id": "linuxmint",
        "id_like": ("ubuntu", "debian"),
        "version_id": "24.04",
        "version_codename": None,
    }

    supported_profiles = [
        {
            "id": "ubuntu",
            "version_id": "24.04",
            "package_manager": "apt-get",
        },
    ]

    with pytest.raises(
        ValueError,
        match=r"unsupported platform: linuxmint 24\.04",
    ):
        select_platform_profile(
            platform,
            supported_profiles,
        )


def test_select_platform_profile_rejects_unsupported_version():
    platform = {
        "id": "ubuntu",
        "id_like": ("debian",),
        "version_id": "22.04",
        "version_codename": "jammy",
    }

    supported_profiles = [
        {
            "id": "ubuntu",
            "version_id": "24.04",
            "package_manager": "apt-get",
        },
    ]

    with pytest.raises(
        ValueError,
        match=r"unsupported platform: ubuntu 22\.04",
    ):
        select_platform_profile(
            platform,
            supported_profiles,
        )


def test_detect_platform_profile_parses_os_release_and_selects_profile():
    os_release = """
ID=ubuntu
ID_LIKE=debian
VERSION_ID="24.04"
VERSION_CODENAME=noble
"""

    supported_profiles = [
        {
            "id": "ubuntu",
            "version_id": "24.04",
            "package_manager": "apt-get",
        },
    ]

    profile = detect_platform_profile(
        os_release,
        supported_profiles,
    )

    assert profile == supported_profiles[0]


def test_read_os_release_reads_declared_path():
    calls = []

    class OsReleasePath:
        def read_text(self, encoding):
            calls.append(encoding)
            return (
                "ID=ubuntu\n"
                'VERSION_ID="24.04"\n'
            )

    content = read_os_release(
        path=OsReleasePath(),
    )

    assert content == (
        "ID=ubuntu\n"
        'VERSION_ID="24.04"\n'
    )
    assert calls == ["utf-8"]