# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from install.prerequisites import (
    build_installation_plan,
    check_prerequisite,
    is_python_venv_available,
    is_python_version_compatible,
)
from pathlib import Path
import pytest

from install.validator import (
    load_install_manifest,
    load_project_metadata,
)


def test_existing_command_satisfies_prerequisite():
    prerequisite = {
        "required": True,
        "command": "tor",
        "package": "tor",
    }

    result = check_prerequisite(
        prerequisite,
        command_exists=lambda command: command == "tor",
    )

    assert result == {
        "satisfied": True,
        "installation_required": False,
    }



def test_missing_command_requires_installation():
    prerequisite = {
        "required": True,
        "command": "tor",
        "package": "tor",
    }

    result = check_prerequisite(
        prerequisite,
        command_exists=lambda command: False,
    )

    assert result == {
        "satisfied": False,
        "installation_required": True,
    }


def test_installation_plan_contains_missing_required_package():
    prerequisites = {
        "tor": {
            "required": True,
            "command": "tor",
            "package": "tor",
        },
    }

    plan = build_installation_plan(
        prerequisites,
        command_exists=lambda command: False,
    )

    assert plan == {
        "packages": ["tor"],
    }


def test_installation_plan_is_empty_when_required_command_exists():
    prerequisites = {
        "tor": {
            "required": True,
            "command": "tor",
            "package": "tor",
        },
    }

    plan = build_installation_plan(
        prerequisites,
        command_exists=lambda command: True,
    )

    assert plan == {
        "packages": [],
    }


def test_python_3_12_satisfies_project_python_requirement():
    assert is_python_version_compatible(
        (3, 12, 3),
        ">=3.12",
    ) is True


def test_current_python_satisfies_requirement_loaded_from_project_metadata():
    project_root = Path(__file__).resolve().parents[1]
    metadata = load_project_metadata(project_root / "pyproject.toml")

    assert is_python_version_compatible(
        (3, 12, 3),
        metadata["requires-python"],
    ) is True


def test_python_venv_is_available_when_module_check_succeeds():
    assert is_python_venv_available(
        module_available=lambda module: module == "venv",
    ) is True


def test_python_venv_is_not_available_when_module_check_fails():
    assert is_python_venv_available(
        module_available=lambda module: False,
    ) is False


def test_installation_plan_requires_python_venv_when_python_exists_but_venv_is_missing():
    prerequisites = {
        "python_venv": {
            "required": True,
            "command": "python3",
            "package": "python3-venv",
        },
    }

    plan = build_installation_plan(
        prerequisites,
        command_exists=lambda command: True,
        python_venv_available=lambda: False,
    )

    assert plan == {
        "packages": ["python3-venv"],
    }


def test_installation_plan_rejects_missing_python_venv_detector():
    prerequisites = {
        "python_venv": {
            "required": True,
            "command": "python3",
            "package": "python3-venv",
        },
    }

    with pytest.raises(
        ValueError,
        match="python_venv_available detector is required",
    ):
        build_installation_plan(
            prerequisites,
            command_exists=lambda command: True,
        )


def test_installation_plan_rejects_incompatible_python_version():
    prerequisites = {
        "python_venv": {
            "required": True,
            "command": "python3",
            "package": "python3-venv",
        },
    }

    with pytest.raises(
        ValueError,
        match="Python version does not satisfy project requirement",
    ):
        build_installation_plan(
            prerequisites,
            command_exists=lambda command: True,
            python_venv_available=lambda: True,
            python_version=(3, 11, 9),
            python_requirement=">=3.12",
        )


def test_installation_plan_requires_no_python_package_when_python_and_venv_are_compatible():
    prerequisites = {
        "python_venv": {
            "required": True,
            "command": "python3",
            "package": "python3-venv",
        },
    }

    plan = build_installation_plan(
        prerequisites,
        command_exists=lambda command: True,
        python_venv_available=lambda: True,
        python_version=(3, 12, 3),
        python_requirement=">=3.12",
    )

    assert plan == {
        "packages": [],
    }


def test_real_repository_metadata_builds_empty_plan_when_prerequisites_are_satisfied():
    project_root = Path(__file__).resolve().parents[1]

    manifest = load_install_manifest(
        project_root / "install" / "manifest.toml"
    )
    metadata = load_project_metadata(
        project_root / "pyproject.toml"
    )

    profile = manifest["platform"]["profiles"][0]

    plan = build_installation_plan(
        profile["system_prerequisites"],
        command_exists=lambda command: True,
        python_venv_available=lambda: True,
        python_version=(3, 12, 3),
        python_requirement=metadata["requires-python"],
    )

    assert plan == {
        "packages": [],
    }


def test_real_repository_metadata_builds_plan_for_missing_tor_and_python_venv():
    project_root = Path(__file__).resolve().parents[1]

    manifest = load_install_manifest(
        project_root / "install" / "manifest.toml"
    )
    metadata = load_project_metadata(
        project_root / "pyproject.toml"
    )

    profile = manifest["platform"]["profiles"][0]

    plan = build_installation_plan(
        profile["system_prerequisites"],
        command_exists=lambda command: False,
        python_venv_available=lambda: False,
        python_version=(3, 12, 3),
        python_requirement=metadata["requires-python"],
    )

    assert plan == {
        "packages": ["tor", "python3-venv"],
    }