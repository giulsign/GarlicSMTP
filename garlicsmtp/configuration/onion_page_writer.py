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


_KEYS = (
    "onion_custom_page_enabled",
    "onion_custom_page_path",
)

_SECTION = re.compile(r"^\s*\[([^\]]+)\]\s*(?:#.*)?$")
_KEY = re.compile(
    r"^(\s*)(onion_custom_page_enabled|onion_custom_page_path)"
    r"(\s*=\s*)(.*)$"
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
    path = Path(path)

    if not isinstance(enabled, bool):
        raise TypeError("enabled must be a bool")

    if not isinstance(html_path, str):
        raise TypeError("html_path must be a string")

    original = path.read_text(encoding="utf-8")

    # Reject invalid input rather than accidentally repairing or
    # overwriting unrelated configuration.
    tomllib.loads(original)

    values = {
        "onion_custom_page_enabled": (
            "true" if enabled else "false"
        ),
        "onion_custom_page_path": json.dumps(
            html_path,
            ensure_ascii=True,
        ),
    }

    lines = original.splitlines(keepends=True)
    result = []
    inside_tor = False
    tor_found = False
    written = set()

    def append_missing():
        if result and not result[-1].endswith(("\n", "\r")):
            result.append("\n")

        for key in _KEYS:
            if key not in written:
                result.append(f"{key} = {values[key]}\n")
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
                    f"{match.group(3)}{values[key]}"
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

    if (
        parsed["tor"]["onion_custom_page_enabled"]
        is not enabled
        or parsed["tor"]["onion_custom_page_path"]
        != html_path
    ):
        raise ValueError("Failed to update Onion page settings")

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
