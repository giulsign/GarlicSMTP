# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0

# See LICENSE for the full license terms.

from pathlib import Path

import pytest

from install.tor_config import (
    build_tor_configuration_actions,
    build_tor_configuration_plan,
    execute_tor_configuration_plan,
    tor_managed_block_present,
)


def test_build_tor_configuration_plan_adds_local_control_port():
    plan = build_tor_configuration_plan(
        tor_state="configuration_required",
        torrc_path=Path("/etc/tor/torrc"),
        runtime_user="alice",
        control_host="127.0.0.1",
        control_port=9051,
    )

    assert plan["torrc_path"] == Path(
        "/etc/tor/torrc"
    )

    assert (
        "ControlPort 127.0.0.1:9051"
        in plan["append_text"]
    )


def test_build_tor_configuration_plan_does_not_create_hidden_service():
    plan = build_tor_configuration_plan(
        tor_state="configuration_required",
        torrc_path=Path("/etc/tor/torrc"),
        runtime_user="alice",
        control_host="127.0.0.1",
        control_port=9051,
    )

    assert "HiddenServiceDir" not in plan["append_text"]
    assert "HiddenServicePort" not in plan["append_text"]


def test_build_tor_configuration_plan_grants_rootless_cookie_access():
    plan = build_tor_configuration_plan(
        tor_state="configuration_required",
        torrc_path=Path("/etc/tor/torrc"),
        runtime_user="alice",
        control_host="127.0.0.1",
        control_port=9051,
    )

    assert plan["group_membership"] == {
        "user": "alice",
        "group": "debian-tor",
    }

    assert plan["requires_privileges"] is True


def test_build_tor_configuration_plan_rejects_non_configuration_required_state():
    with pytest.raises(
        RuntimeError,
        match="configuration_required",
    ):
        build_tor_configuration_plan(
            tor_state="compatible",
            torrc_path=Path("/etc/tor/torrc"),
            runtime_user="alice",
            control_host="127.0.0.1",
            control_port=9051,
        )


def test_execute_tor_configuration_plan_executes_all_system_actions():
    plan = build_tor_configuration_plan(
        tor_state="configuration_required",
        torrc_path=Path("/etc/tor/torrc"),
        runtime_user="alice",
        control_host="127.0.0.1",
        control_port=9051,
    )

    calls = []

    profile = {
        "privilege_elevation": "sudo",
    }

    runner = object()

    def execute_action(profile_arg, action, run_arg):
        calls.append(
            (profile_arg, action, run_arg)
        )

    execute_tor_configuration_plan(
        plan,
        profile=profile,
        run=runner,
        execute_action=execute_action,
    )

    actions = build_tor_configuration_actions(plan)

    assert calls == [
        (profile, actions[0], runner),
        (profile, actions[1], runner),
        (profile, actions[2], runner),
    ]


def test_execute_tor_configuration_plan_stops_if_torrc_action_fails():
    plan = build_tor_configuration_plan(
        tor_state="configuration_required",
        torrc_path=Path("/etc/tor/torrc"),
        runtime_user="alice",
        control_host="127.0.0.1",
        control_port=9051,
    )

    calls = []

    profile = {
        "privilege_elevation": "sudo",
    }

    runner = object()

    def execute_action(profile_arg, action, run_arg):
        calls.append(action)

        if action["command"][0] == "tee":
            raise OSError("write failed")

    with pytest.raises(
        OSError,
        match="write failed",
    ):
        execute_tor_configuration_plan(
            plan,
            profile=profile,
            run=runner,
            execute_action=execute_action,
        )

    actions = build_tor_configuration_actions(plan)

    assert calls == [
        actions[0],
    ]


def test_execute_tor_configuration_plan_stops_if_system_action_fails():
    plan = build_tor_configuration_plan(
        tor_state="configuration_required",
        torrc_path=Path("/etc/tor/torrc"),
        runtime_user="alice",
        control_host="127.0.0.1",
        control_port=9051,
    )

    calls = []

    profile = {
        "privilege_elevation": "sudo",
    }

    runner = object()

    def execute_action(profile_arg, action, run_arg):
        calls.append(action)

        if action["command"][0] == "usermod":
            raise RuntimeError(
                "group update failed"
            )

    with pytest.raises(
        RuntimeError,
        match="group update failed",
    ):
        execute_tor_configuration_plan(
            plan,
            profile=profile,
            run=runner,
            execute_action=execute_action,
        )

    actions = build_tor_configuration_actions(plan)

    assert calls == [
        actions[0],
        actions[1],
    ]


def test_build_tor_configuration_actions_builds_privileged_actions():
    plan = build_tor_configuration_plan(
        tor_state="configuration_required",
        torrc_path=Path("/etc/tor/torrc"),
        runtime_user="alice",
        control_host="127.0.0.1",
        control_port=9051,
    )

    actions = build_tor_configuration_actions(plan)

    assert actions == [
        {
            "command": [
                "tee",
                "-a",
                "/etc/tor/torrc",
            ],
            "requires_privileges": True,
            "input": plan["append_text"],
        },
        {
            "command": [
                "usermod",
                "-a",
                "-G",
                "debian-tor",
                "alice",
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


def test_build_tor_configuration_actions_does_not_embed_sudo():
    plan = build_tor_configuration_plan(
        tor_state="configuration_required",
        torrc_path=Path("/etc/tor/torrc"),
        runtime_user="alice",
        control_host="127.0.0.1",
        control_port=9051,
    )

    actions = build_tor_configuration_actions(plan)

    assert all(
        action["command"][0] != "sudo"
        for action in actions
    )


def test_execute_tor_configuration_plan_requires_no_direct_file_writer():
    plan = build_tor_configuration_plan(
        tor_state="configuration_required",
        torrc_path=Path("/etc/tor/torrc"),
        runtime_user="alice",
        control_host="127.0.0.1",
        control_port=9051,
    )

    profile = {
        "privilege_elevation": "sudo",
    }

    calls = []

    def execute_action(profile_arg, action, run_arg):
        calls.append(action)

    execute_tor_configuration_plan(
        plan,
        profile=profile,
        run=object(),
        execute_action=execute_action,
    )

    assert len(calls) == 3
    assert calls[0]["command"] == [
        "tee",
        "-a",
        "/etc/tor/torrc",
    ]


def test_tor_configuration_plan_marks_managed_block():
    plan = build_tor_configuration_plan(
        tor_state="configuration_required",
        torrc_path=Path("/etc/tor/torrc"),
        runtime_user="alice",
        control_host="127.0.0.1",
        control_port=9051,
    )

    assert plan["marker"] == "# GarlicSMTP Tor Control"
    assert plan["marker"] in plan["append_text"]


def test_tor_configuration_actions_skip_append_when_managed_block_exists(
    tmp_path,
):
    torrc_path = tmp_path / "torrc"
    torrc_path.write_text(
        "\n# GarlicSMTP Tor Control\n"
        "ControlPort 127.0.0.1:9051\n",
        encoding="utf-8",
    )

    plan = build_tor_configuration_plan(
        tor_state="configuration_required",
        torrc_path=torrc_path,
        runtime_user="alice",
        control_host="127.0.0.1",
        control_port=9051,
    )

    actions = build_tor_configuration_actions(
        plan,
        managed_block_present=True,
    )

    commands = [action["command"] for action in actions]

    assert ["tee", "-a", str(torrc_path)] not in commands
    assert ["usermod", "-a", "-G", "debian-tor", "alice"] in commands
    assert [
        "systemctl",
        "restart",
        "tor@default.service",
    ] in commands


def test_tor_managed_block_detection_finds_existing_block(
    tmp_path,
):
    torrc_path = tmp_path / "torrc"
    torrc_path.write_text(
        "\n# GarlicSMTP Tor Control\n"
        "ControlPort 127.0.0.1:9051\n",
        encoding="utf-8",
    )

    assert tor_managed_block_present(
        torrc_path=torrc_path,
        marker="# GarlicSMTP Tor Control",
    ) is True


def test_execute_tor_configuration_plan_resumes_after_managed_block(
    tmp_path,
):
    torrc_path = tmp_path / "torrc"

    plan = build_tor_configuration_plan(
        tor_state="configuration_required",
        torrc_path=torrc_path,
        runtime_user="alice",
        control_host="127.0.0.1",
        control_port=9051,
    )

    executed = []

    def execute_action(profile, action, run):
        executed.append(action)

    execute_tor_configuration_plan(
        plan,
        profile={"privilege_elevation": "sudo"},
        run=lambda command, **kwargs: None,
        execute_action=execute_action,
        managed_block_detector=lambda **kwargs: True,
    )

    assert [
        action["command"]
        for action in executed
    ] == [
        [
            "usermod",
            "-a",
            "-G",
            "debian-tor",
            "alice",
        ],
        [
            "systemctl",
            "restart",
            "tor@default.service",
        ],
    ]