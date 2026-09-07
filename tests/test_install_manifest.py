# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from pathlib import Path
import tomllib


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INSTALL_MANIFEST = PROJECT_ROOT / "install" / "manifest.toml"


def load_install_manifest():
    with INSTALL_MANIFEST.open("rb") as manifest_file:
        return tomllib.load(manifest_file)


def test_install_manifest_declares_supported_schema():
    manifest = load_install_manifest()

    assert manifest["schema_version"] == 1


def test_install_manifest_targets_linux():
    manifest = load_install_manifest()

    assert manifest["platform"]["os"] == "linux"


def test_install_manifest_rejects_project_metadata_duplication():
    from install.validator import validate_manifest

    manifest = load_install_manifest()
    manifest["project"] = {
        "version": "0.1.0-alpha",
        "requires-python": ">=3.12",
        "dependencies": ["dnspython>=2.8,<3"],
    }

    errors = validate_manifest(manifest)

    assert errors == [
        "manifest must not declare project.version",
        "manifest must not declare project.requires-python",
        "manifest must not declare project.dependencies",
    ]


def test_current_install_manifest_is_valid():
    from install.validator import validate_manifest

    manifest = load_install_manifest()

    assert validate_manifest(manifest) == []


def test_project_metadata_is_loaded_from_pyproject():
    from install.validator import load_project_metadata

    metadata = load_project_metadata(PROJECT_ROOT / "pyproject.toml")

    assert metadata == {
        "version": "0.1.0-alpha",
        "requires-python": ">=3.12",
        "dependencies": [
            "dnspython>=2.8,<3",
            "PySide6>=6.11,<7",
            "cryptography>=46,<47",
        ],
    }


def test_current_repository_installation_metadata_is_valid():
    from install.validator import validate_repository

    assert validate_repository(PROJECT_ROOT) == []


def test_repository_validation_rejects_duplicated_project_metadata(tmp_path):
    from install.validator import validate_repository

    (tmp_path / "install").mkdir()

    (tmp_path / "pyproject.toml").write_text(
        """
[project]
version = "1.2.3"
requires-python = ">=3.12"
dependencies = ["example>=1"]
""".strip(),
        encoding="utf-8",
    )

    (tmp_path / "install" / "manifest.toml").write_text(
        """
schema_version = 1

[platform]
os = "linux"

[project]
version = "1.2.3"
""".strip(),
        encoding="utf-8",
    )

    assert validate_repository(tmp_path) == [
        "manifest must not declare project.version",
    ]


def test_install_manifest_rejects_unsupported_schema():
    from install.validator import validate_manifest

    manifest = {
        "schema_version": 2,
        "platform": {
            "os": "linux",
        },
    }

    assert validate_manifest(manifest) == [
        "unsupported manifest schema_version: 2",
    ]


def test_install_manifest_rejects_missing_schema():
    from install.validator import validate_manifest

    manifest = {
        "platform": {
            "os": "linux",
        },
    }

    assert validate_manifest(manifest) == [
        "manifest schema_version is required",
    ]


def test_install_manifest_rejects_unsupported_operating_system():
    from install.validator import validate_manifest

    manifest = {
        "schema_version": 1,
        "platform": {
            "os": "windows",
        },
    }

    assert validate_manifest(manifest) == [
        "unsupported platform.os: windows",
    ]


def test_install_manifest_rejects_missing_operating_system():
    from install.validator import validate_manifest

    manifest = {
        "schema_version": 1,
        "platform": {},
    }

    assert validate_manifest(manifest) == [
        "manifest platform.os is required",
    ]


def test_install_manifest_declares_ubuntu_24_04_profile():
    manifest = load_install_manifest()

    profile = manifest["platform"]["profiles"][0]

    assert profile["id"] == "ubuntu"
    assert profile["version_id"] == "24.04"


def test_ubuntu_24_04_profile_declares_package_manager():
    manifest = load_install_manifest()

    profile = manifest["platform"]["profiles"][0]

    assert profile["package_manager"] == "apt-get"


def test_ubuntu_24_04_profile_declares_tor_system_prerequisite():
    manifest = load_install_manifest()

    profile = manifest["platform"]["profiles"][0]

    assert profile["system_prerequisites"]["tor"]["required"] is True


def test_tor_prerequisite_declares_detection_command():
    manifest = load_install_manifest()

    tor = (
        manifest["platform"]["profiles"][0]
        ["system_prerequisites"]["tor"]
    )

    assert tor["command"] == "tor"


def test_tor_prerequisite_declares_ubuntu_package():
    manifest = load_install_manifest()

    tor = (
        manifest["platform"]["profiles"][0]
        ["system_prerequisites"]["tor"]
    )

    assert tor["package"] == "tor"


def test_ubuntu_24_04_profile_declares_python_venv_prerequisite():
    manifest = load_install_manifest()

    python_venv = (
        manifest["platform"]["profiles"][0]
        ["system_prerequisites"]["python_venv"]
    )

    assert python_venv == {
        "required": True,
        "command": "python3",
        "package": "python3-venv",
    }