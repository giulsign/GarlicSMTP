# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import runpy
import pytest

import garlicsmtp.gui.application as gui_application


def test_gui_module_runs_with_development_paths(
    tmp_path,
    monkeypatch,
):
    from garlicsmtp.configuration import (
        ApplicationPaths,
    )

    expected_paths = (
        ApplicationPaths.for_development(
            project_root=tmp_path,
            home=tmp_path,
        )
    )

    received = {}

    monkeypatch.setattr(
        gui_application.ApplicationPaths,
        "for_development",
        lambda: expected_paths,
    )

    def fake_run_gui(
        *,
        paths=None,
    ):
        received["paths"] = paths
        return 0

    monkeypatch.setattr(
        gui_application,
        "run_gui",
        fake_run_gui,
    )

    with pytest.raises(SystemExit) as exc_info:
        runpy.run_module(
            "garlicsmtp.gui",
            run_name="__main__",
        )

    assert exc_info.value.code == 0
    assert received["paths"] == expected_paths
