# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from install.platform import is_supported_platform, parse_os_release


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
