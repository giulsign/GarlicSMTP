# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0

# See LICENSE for the full license terms.

import os
from pathlib import Path

from garlicsmtp.tor.control import (
    TorControlClient,
    TorControlConnection,
)


def _cookie_is_readable(path: Path) -> bool:
    return os.access(path, os.R_OK)


def _build_tor_control_client(
    *,
    control_host: str,
    control_port: int,
) -> TorControlClient:
    connection = TorControlConnection(
        host=control_host,
        port=control_port,
    )

    return TorControlClient(
        connection=connection,
    )


def detect_tor_runtime_configuration(
    *,
    control_host: str,
    control_port: int,
    client=None,
    client_factory=None,
    cookie_readable=_cookie_is_readable,
) -> dict:
    if client is not None and client_factory is not None:
        raise ValueError(
            "client and client_factory are mutually exclusive"
        )

    if client is None:
        factory = (
            client_factory
            or _build_tor_control_client
        )

        client = factory(
            control_host=control_host,
            control_port=control_port,
        )

    client.connect()

    try:
        protocol_info = client.protocol_info()

        if not protocol_info.supports_safecookie:
            raise RuntimeError(
                "Tor Control endpoint does not support SAFECOOKIE"
            )

        if protocol_info.cookie_file is None:
            raise RuntimeError(
                "Tor Control endpoint did not advertise a cookie file"
            )

        cookie_file = protocol_info.cookie_file

        if not cookie_readable(cookie_file):
            raise RuntimeError(
                "Tor Control cookie is not readable: "
                f"{cookie_file}"
            )

        return {
            "control_host": control_host,
            "control_port": control_port,
            "cookie_file": cookie_file,
        }
    finally:
        client.close()


def create_runtime_configuration(
    *,
    settings_file: Path,
    tor_configuration: dict,
) -> None:
    settings_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    cookie_file = tor_configuration["cookie_file"]

    content = (
        "[tor]\n"
        "control_enabled = true\n"
        f'control_host = "{tor_configuration["control_host"]}"\n'
        f'control_port = {tor_configuration["control_port"]}\n'
        f'cookie_file = "{cookie_file}"\n'
    )

    with settings_file.open(
        "x",
        encoding="utf-8",
    ) as file:
        file.write(content)


def validate_runtime_configuration(
    settings,
    *,
    cookie_readable=_cookie_is_readable,
) -> None:
    if not settings.tor.enabled:
        raise RuntimeError(
            "Tor must be enabled"
        )

    if not settings.tor.control_enabled:
        raise RuntimeError(
            "Tor Control must be enabled"
        )

    if settings.tor.cookie_file is None:
        raise RuntimeError(
            "Tor Control cookie file is required"
        )

    if not settings.tor.require_safecookie:
        raise RuntimeError(
            "SAFECOOKIE must be required"
        )

    if not cookie_readable(
        settings.tor.cookie_file,
    ):
        raise RuntimeError(
            "Tor Control cookie is not readable"
        )