# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from pathlib import Path
import tomllib


SUPPORTED_SCHEMA_VERSION = 1

SUPPORTED_OPERATING_SYSTEM = "linux"

SUPPORTED_PRIVILEGE_ELEVATION = "sudo"

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

    for profile in platform.get("profiles", []):
        privilege_elevation = profile.get("privilege_elevation")

        if privilege_elevation is None:
            errors.append("profile privilege_elevation is required")
        elif privilege_elevation != SUPPORTED_PRIVILEGE_ELEVATION:
            errors.append(
                "unsupported privilege_elevation: "
                f"{privilege_elevation}"
            )

        tor = (
            profile.get("system_prerequisites", {})
            .get("tor", {})
        )

        control = tor.get("control", {})

        control_host = control.get("host")

        if (
            control_host is not None
            and control_host != "127.0.0.1"
        ):
            errors.append(
                "Tor Control host must be local loopback"
            )

        control_authentication = control.get("authentication")

        if (
            control_authentication is not None
            and control_authentication != "safecookie"
        ):
            errors.append(
                "Tor Control authentication must be safecookie"
            )

        cookie_path_source = control.get("cookie_path_source")

        if (
            cookie_path_source is not None
            and cookie_path_source != "protocolinfo"
        ):
            errors.append(
                "Tor Control cookie path source must be protocolinfo"
            )

        cookie_access = control.get("cookie_access", {})

        runtime_user_rootless = cookie_access.get(
            "runtime_user_rootless"
        )

        if runtime_user_rootless is False:
            errors.append(
                "Tor Control cookie access must be rootless at runtime"
            )

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
