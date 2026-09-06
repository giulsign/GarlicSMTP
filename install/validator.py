# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from pathlib import Path
import tomllib


SUPPORTED_SCHEMA_VERSION = 1

SUPPORTED_OPERATING_SYSTEM = "linux"

PROJECT_METADATA_KEYS = (
    "version",
    "requires-python",
    "dependencies",
)


def load_project_metadata(pyproject_path: Path) -> dict:
    with pyproject_path.open("rb") as pyproject_file:
        pyproject = tomllib.load(pyproject_file)

    project = pyproject["project"]

    return {
        "version": project["version"],
        "requires-python": project["requires-python"],
        "dependencies": project["dependencies"],
    }


def load_install_manifest(manifest_path: Path) -> dict:
    with manifest_path.open("rb") as manifest_file:
        return tomllib.load(manifest_file)


def validate_manifest(manifest: dict) -> list[str]:
    errors = []

    schema_version = manifest.get("schema_version")
    if schema_version is None:
        errors.append("manifest schema_version is required")
    elif schema_version != SUPPORTED_SCHEMA_VERSION:
        errors.append(
            f"unsupported manifest schema_version: {schema_version}"
        )

    platform = manifest.get("platform", {})
    operating_system = platform.get("os")

    if operating_system is None:
        errors.append("manifest platform.os is required")
    elif operating_system != SUPPORTED_OPERATING_SYSTEM:
        errors.append(
            f"unsupported platform.os: {operating_system}"
        )

    project = manifest.get("project", {})

    for key in PROJECT_METADATA_KEYS:
        if key in project:
            errors.append(f"manifest must not declare project.{key}")

    return errors


def validate_repository(project_root: Path) -> list[str]:
    load_project_metadata(project_root / "pyproject.toml")
    manifest = load_install_manifest(project_root / "install" / "manifest.toml")

    return validate_manifest(manifest)
