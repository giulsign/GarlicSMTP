# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import tkinter as tk
from tkinter import ttk

from garlicsmtp.gui.tk_theme import (
    GarlicTheme,
    configure_garlic_theme,
)


def test_garlic_theme_configures_core_palette():
    root = tk.Tk()
    root.withdraw()

    try:
        style = ttk.Style(root)

        configure_garlic_theme(style)

        assert GarlicTheme.FRAME_BACKGROUND == "#000000"
        assert GarlicTheme.TEXT_FOREGROUND == "#ff8c00"
        assert GarlicTheme.INPUT_BACKGROUND == "#ffffff"
        assert GarlicTheme.INPUT_FOREGROUND == "#000000"
        assert GarlicTheme.SELECTION_BACKGROUND == "#ff8c00"

        assert (
            style.lookup(
                "Garlic.TFrame",
                "background",
            )
            == GarlicTheme.FRAME_BACKGROUND
        )

        assert (
            style.lookup(
                "Garlic.TLabel",
                "foreground",
            )
            == GarlicTheme.TEXT_FOREGROUND
        )

    finally:
        root.destroy()


def test_garlic_theme_configures_text_input_palette():
    root = tk.Tk()
    root.withdraw()

    try:
        style = ttk.Style(root)

        configure_garlic_theme(style)

        assert (
            style.lookup(
                "Garlic.TEntry",
                "fieldbackground",
            )
            == GarlicTheme.INPUT_BACKGROUND
        )

        assert (
            style.lookup(
                "Garlic.TEntry",
                "foreground",
            )
            == GarlicTheme.INPUT_FOREGROUND
        )

        assert (
            style.lookup(
                "Garlic.TEntry",
                "selectbackground",
            )
            == GarlicTheme.SELECTION_BACKGROUND
        )

    finally:
        root.destroy()