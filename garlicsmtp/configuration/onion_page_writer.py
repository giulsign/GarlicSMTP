# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from pathlib import Path
import json
import re
import tomllib
import os
import tempfile
import stat


_CUSTOM_KEYS = (
    "onion_custom_page_enabled",
    "onion_custom_page_path",
)

_WEBSITE_KEYS = (
    "onion_website_enabled",
    "onion_website_index_path",
)

_SECTION = re.compile(r"^\s*\[([^\]]+)\]\s*(?:#.*)?$")
_KEY = re.compile(
    r"^(\s*)("
    r"onion_custom_page_enabled|onion_custom_page_path|"
    r"onion_website_enabled|onion_website_index_path"
    r")(\s*=\s*)(.*)$"
)


def _split_inline_comment(value: str) -> tuple[str, str]:
    in_string = False
    escaped = False

    for index, char in enumerate(value):
        if escaped:
            escaped = False
            continue

        if char == "\\" and in_string:
            escaped = True
            continue

        if char == '"':
            in_string = not in_string
            continue

        if char == "#" and not in_string:
            return value[:index].rstrip(), value[index:]

    return value.rstrip(), ""


def save_onion_page_settings(
    path: Path,
    *,
    enabled: bool,
    html_path: str,
) -> None:
    _save_onion_settings(
        path,
        values={
            _CUSTOM_KEYS[0]: enabled,
            _CUSTOM_KEYS[1]: html_path,
        },
    )


def save_onion_website_settings(
    path: Path,
    *,
    enabled: bool,
    html_path: str,
) -> None:
    _save_onion_settings(
        path,
        values={
            _WEBSITE_KEYS[0]: enabled,
            _WEBSITE_KEYS[1]: html_path,
        },
    )


def save_onion_combined_settings(
    path: Path,
    *,
    custom_enabled: bool,
    custom_html_path: str,
    website_enabled: bool,
    website_index_path: str,
) -> None:
    _save_onion_settings(
        path,
        values={
            _CUSTOM_KEYS[0]: custom_enabled,
            _CUSTOM_KEYS[1]: custom_html_path,
            _WEBSITE_KEYS[0]: website_enabled,
            _WEBSITE_KEYS[1]: website_index_path,
        },
    )


def _save_onion_settings(
    path: Path,
    *,
    values: dict[str, bool | str],
) -> None:
    path = Path(path)

    allowed_keys = set(_CUSTOM_KEYS + _WEBSITE_KEYS)
    if not values or not set(values).issubset(allowed_keys):
        raise ValueError("Invalid Onion settings keys")

    for key, value in values.items():
        if key.endswith("_enabled"):
            if not isinstance(value, bool):
                raise TypeError(f"{key} must be a bool")
        elif not isinstance(value, str):
            raise TypeError(f"{key} must be a string")

    original = path.read_text(encoding="utf-8")

    # Reject invalid input rather than accidentally repairing or
    # overwriting unrelated configuration.
    tomllib.loads(original)

    serialized_values = {
        key: (
            "true" if value else "false"
        ) if isinstance(value, bool) else json.dumps(
            value,
            ensure_ascii=True,
        )
        for key, value in values.items()
    }
    keys = tuple(values)

    lines = original.splitlines(keepends=True)
    result = []
    inside_tor = False
    tor_found = False
    written = set()

    def append_missing():
        if result and not result[-1].endswith(("\n", "\r")):
            result.append("\n")

        for key in keys:
            if key not in written:
                result.append(f"{key} = {serialized_values[key]}\n")
                written.add(key)

    for line in lines:
        section = _SECTION.match(line.rstrip("\r\n"))

        if section:
            if inside_tor:
                append_missing()

            inside_tor = section.group(1).strip() == "tor"

            if inside_tor:
                tor_found = True

        if inside_tor:
            match = _KEY.match(line.rstrip("\r\n"))

            if match:
                key = match.group(2)

                if key not in keys:
                    result.append(line)
                    continue

                if key in written:
                    raise ValueError(
                        f"Duplicate Onion page setting: {key}"
                    )

                newline = (
                    "\r\n" if line.endswith("\r\n")
                    else "\n" if line.endswith("\n")
                    else ""
                )

                _, comment = _split_inline_comment(match.group(4))
                separator = " " if comment else ""

                result.append(
                    f"{match.group(1)}{key}"
                    f"{match.group(3)}{serialized_values[key]}"
                    f"{separator}{comment}{newline}"
                )
                written.add(key)
                continue

        result.append(line)

    if inside_tor:
        append_missing()

    if not tor_found:
        if result and not result[-1].endswith(("\n", "\r")):
            result.append("\n")

        result.append("\n[tor]\n")
        append_missing()

    updated = "".join(result)

    # Verify the resulting TOML before replacing the file.
    parsed = tomllib.loads(updated)
    for key, expected_value in values.items():
        actual_value = parsed["tor"][key]
        if type(actual_value) is not type(expected_value):
            raise ValueError(f"Invalid type for Onion setting: {key}")
        if actual_value != expected_value:
            raise ValueError(f"Failed to update Onion setting: {key}")

    original_mode = stat.S_IMODE(path.stat().st_mode)
    temporary_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            temporary_file.write(updated)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())

        os.chmod(temporary_path, original_mode)
        os.replace(temporary_path, path)

    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
