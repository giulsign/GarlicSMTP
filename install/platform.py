# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from pathlib import Path


def parse_os_release(content: str) -> dict:
    values = {}

    for line in content.splitlines():
        line = line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        value = value.strip()

        if (
            len(value) >= 2
            and value[0] == value[-1]
            and value[0] in {'"', "'"}
        ):
            value = value[1:-1]

        values[key] = value

    return {
        "id": values.get("ID"),
        "id_like": tuple(values.get("ID_LIKE", "").split()),
        "version_id": values.get("VERSION_ID"),
        "version_codename": values.get("VERSION_CODENAME"),
    }


def is_supported_platform(
    platform: dict,
    supported_profiles: list[dict],
) -> bool:
    for profile in supported_profiles:
        if (
            platform.get("id") == profile.get("id")
            and platform.get("version_id") == profile.get("version_id")
        ):
            return True

    return False


def select_platform_profile(
    platform: dict,
    supported_profiles: list[dict],
) -> dict:
    for profile in supported_profiles:
        if (
            platform.get("id") == profile.get("id")
            and platform.get("version_id") == profile.get("version_id")
        ):
            return profile

    raise ValueError(
        "unsupported platform: "
        f"{platform.get('id')} "
        f"{platform.get('version_id')}"
    )


def detect_platform_profile(
    os_release: str,
    supported_profiles: list[dict],
) -> dict:
    platform = parse_os_release(os_release)

    return select_platform_profile(
        platform,
        supported_profiles,
    )


def read_os_release(
    path: Path = Path("/etc/os-release"),
) -> str:
    return path.read_text(encoding="utf-8")