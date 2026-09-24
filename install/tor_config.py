# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0

# See LICENSE for the full license terms.
from pathlib import Path

TOR_MANAGED_MARKER = "# GarlicSMTP Tor Control"

def build_tor_configuration_plan(
    *,
    tor_state: str,
    torrc_path: Path,
    runtime_user: str,
    control_host: str,
    control_port: int,
) -> dict:
    if tor_state != "configuration_required":
        raise RuntimeError(
            "Tor state must be configuration_required"
        )

    append_text = (
        "\n"
        f"{TOR_MANAGED_MARKER}\n"
        f"ControlPort {control_host}:{control_port}\n"
    )

    return {
        "torrc_path": torrc_path,
        "marker": TOR_MANAGED_MARKER,
        "append_text": append_text,
        "group_membership": {
            "user": runtime_user,
            "group": "debian-tor",
        },
        "requires_privileges": True,
    }


def build_tor_configuration_actions(
    plan: dict,
    *,
    managed_block_present: bool = False,
) -> list[dict]:
    membership = plan["group_membership"]

    actions = []

    if not managed_block_present:
        actions.append(
            {
                "command": [
                    "tee",
                    "-a",
                    str(plan["torrc_path"]),
                ],
                "requires_privileges": True,
                "input": plan["append_text"],
            }
        )

    actions.extend(
        [
            {
                "command": [
                    "usermod",
                    "-a",
                    "-G",
                    membership["group"],
                    membership["user"],
                ],
                "requires_privileges": True,
            },
            {
                "command": [
                    "systemctl",
                    "restart",
                    "tor@default.service",
                ],
                "requires_privileges": True,
            },
        ]
    )

    return actions


def tor_managed_block_present(
    *,
    torrc_path: Path,
    marker: str,
) -> bool:
    if not torrc_path.exists():
        return False

    return marker in torrc_path.read_text(
        encoding="utf-8",
    )


def execute_tor_configuration_plan(
    plan: dict,
    *,
    profile: dict,
    run,
    execute_action,
    managed_block_detector=tor_managed_block_present,
) -> None:
    managed_block_present = managed_block_detector(
        torrc_path=plan["torrc_path"],
        marker=plan["marker"],
    )

    actions = build_tor_configuration_actions(
        plan,
        managed_block_present=managed_block_present,
    )

    for action in actions:
        execute_action(
            profile,
            action,
            run,
        )