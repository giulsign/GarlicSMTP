# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0

# See LICENSE for the full license terms.

import os

from pathlib import Path

import pytest

from install.generator import generate_installer


def test_generate_installer_rejects_invalid_repository(
    tmp_path,
):
    def validate_repository(project_root):
        assert project_root == tmp_path
        return ["manifest platform.os is required"]

    with pytest.raises(
        ValueError,
        match="manifest platform.os is required",
    ):
        generate_installer(
            project_root=tmp_path,
            validate=validate_repository,
        )


def test_generate_installer_writes_install_script(
    tmp_path,
):
    output = tmp_path / "install.sh"

    result = generate_installer(
        project_root=tmp_path,
        output_path=output,
        validate=lambda project_root: [],
        load_manifest=lambda path: {
            "platform": {
                "profiles": [
                    {
                        "python": {
                            "executable": "/custom/python3",
                        },
                    },
                ],
            },
        },
    )

    assert result == output
    assert output.exists()


def test_generate_installer_makes_script_executable(
    tmp_path,
):
    output = tmp_path / "install.sh"

    generate_installer(
        project_root=tmp_path,
        output_path=output,
        validate=lambda project_root: [],
        load_manifest=lambda path: {
            "platform": {
                "profiles": [
                    {
                        "python": {
                            "executable": "/custom/python3",
                        },
                    },
                ],
            },
        },
    )

    assert os.access(output, os.X_OK)


def test_generate_installer_writes_shell_shebang(
    tmp_path,
):
    output = tmp_path / "install.sh"

    generate_installer(
        project_root=tmp_path,
        output_path=output,
        validate=lambda project_root: [],
        load_manifest=lambda path: {
            "platform": {
                "profiles": [
                    {
                        "python": {
                            "executable": "/custom/python3",
                        },
                    },
                ],
            },
        },
    )

    assert output.read_text(
        encoding="utf-8",
    ).startswith("#!/bin/sh\n")


def test_generate_installer_runs_python_installer(
    tmp_path,
):
    output = tmp_path / "install.sh"

    generate_installer(
        project_root=tmp_path,
        output_path=output,
        validate=lambda project_root: [],
        load_manifest=lambda path: {
            "platform": {
                "profiles": [
                    {
                        "python": {
                            "executable": "/custom/python3",
                        },
                    },
                ],
            },
        },
    )

    assert (
        "/custom/python3 -m install.installer\n"
        in output.read_text(encoding="utf-8")
    )


def test_generate_installer_changes_to_project_root(
    tmp_path,
):
    output = tmp_path / "install.sh"

    generate_installer(
        project_root=tmp_path,
        output_path=output,
        validate=lambda project_root: [],
        load_manifest=lambda path: {
            "platform": {
                "profiles": [
                    {
                        "python": {
                            "executable": "/custom/python3",
                        },
                    },
                ],
            },
        },
    )

    assert (
        'cd "$(dirname "$0")"\n'
        in output.read_text(encoding="utf-8")
    )


def test_generator_main_generates_from_repository_root():
    from install.generator import main

    calls = []

    def generate(**kwargs):
        calls.append(kwargs)

    main(generate=generate)

    assert calls == [
        {
            "project_root": (
                Path(__file__).resolve().parents[1]
            ),
        }
    ]


def test_generator_module_has_main_guard():
    source = (
        Path(__file__).resolve().parents[1]
        / "install"
        / "generator.py"
    ).read_text(encoding="utf-8")

    assert 'if __name__ == "__main__":' in source
    assert "    main()" in source