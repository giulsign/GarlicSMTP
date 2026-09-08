# Copyright (c) Giuliano Signorelli
#
# See LICENSE for the full license terms.

import pytest
from install.system import build_package_install_action


def test_build_package_install_action_uses_profile_package_manager_and_plan():
    profile = {
        "package_manager": "apt-get",
        "system_prerequisites": {
            "tor": {
                "required": True,
                "command": "tor",
                "package": "tor",
            },
            "python_venv": {
                "required": True,
                "command": "python3",
                "package": "python3-venv",
            },
        },
    }
    plan = {
        "packages": [
            "tor",
            "python3-venv",
        ],
    }

    action = build_package_install_action(
        profile,
        plan,
    )

    assert action == {
        "command": [
            "apt-get",
            "install",
            "-y",
            "tor",
            "python3-venv",
        ],
        "requires_privileges": True,
    }


def test_build_package_install_action_returns_none_when_no_packages_required():
    profile = {
        "package_manager": "apt-get",
    }
    plan = {
        "packages": [],
    }

    action = build_package_install_action(
        profile,
        plan,
    )

    assert action is None


def test_build_package_install_action_rejects_unsupported_package_manager():
    profile = {
        "package_manager": "unknown-manager",
    }
    plan = {
        "packages": [
            "tor",
        ],
    }

    with pytest.raises(
        ValueError,
        match="unsupported package manager: unknown-manager",
    ):
        build_package_install_action(
            profile,
            plan,
        )


def test_build_package_install_action_rejects_package_not_declared_by_profile():
    profile = {
        "package_manager": "apt-get",
        "system_prerequisites": {
            "tor": {
                "required": True,
                "command": "tor",
                "package": "tor",
            },
            "python_venv": {
                "required": True,
                "command": "python3",
                "package": "python3-venv",
            },
        },
    }
    plan = {
        "packages": [
            "unexpected-package",
        ],
    }

    with pytest.raises(
        ValueError,
        match="package not declared by profile: unexpected-package",
    ):
        build_package_install_action(
            profile,
            plan,
        )


def test_build_package_install_action_rejects_missing_system_prerequisites():
    profile = {
        "package_manager": "apt-get",
    }
    plan = {
        "packages": [
            "tor",
        ],
    }

    with pytest.raises(
        ValueError,
        match="profile system_prerequisites is required",
    ):
        build_package_install_action(
            profile,
            plan,
        )