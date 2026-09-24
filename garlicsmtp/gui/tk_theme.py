# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from tkinter import ttk


class GarlicTheme:
    FRAME_BACKGROUND = "#000000"
    TEXT_FOREGROUND = "#ff8c00"

    INPUT_BACKGROUND = "#ffffff"
    INPUT_FOREGROUND = "#000000"

    SELECTION_BACKGROUND = "#ff8c00"


def configure_garlic_theme(
    style: ttk.Style,
) -> None:
    style.configure(
        "Garlic.TFrame",
        background=GarlicTheme.FRAME_BACKGROUND,
    )

    style.configure(
        "Garlic.TLabel",
        background=GarlicTheme.FRAME_BACKGROUND,
        foreground=GarlicTheme.TEXT_FOREGROUND,
    )

    style.configure(
        "Garlic.Header.TLabel",
        background=GarlicTheme.FRAME_BACKGROUND,
        foreground=GarlicTheme.TEXT_FOREGROUND,
        font=("", 10, "bold"),
    )

    style.configure(
        "Garlic.TEntry",
        fieldbackground=GarlicTheme.INPUT_BACKGROUND,
        foreground=GarlicTheme.INPUT_FOREGROUND,
        selectbackground=GarlicTheme.SELECTION_BACKGROUND,
    )

    style.configure(
        "Garlic.Card.TFrame",
        background=GarlicTheme.FRAME_BACKGROUND,
    )

    style.configure(
        "Garlic.CardTitle.TLabel",
        background=GarlicTheme.FRAME_BACKGROUND,
        foreground=GarlicTheme.TEXT_FOREGROUND,
        font=("", 11, "bold"),
    )

    style.configure(
        "Garlic.Readonly.TEntry",
        fieldbackground=GarlicTheme.INPUT_BACKGROUND,
        foreground=GarlicTheme.INPUT_FOREGROUND,
        selectbackground=GarlicTheme.SELECTION_BACKGROUND,
    )

    style.configure(
        "Garlic.Treeview",
        background=GarlicTheme.INPUT_BACKGROUND,
        fieldbackground=GarlicTheme.INPUT_BACKGROUND,
        foreground=GarlicTheme.INPUT_FOREGROUND,
    )

    style.map(
        "Garlic.Treeview",
        background=[
            (
                "selected",
                GarlicTheme.SELECTION_BACKGROUND,
            ),
        ],
        foreground=[
            (
                "selected",
                GarlicTheme.INPUT_FOREGROUND,
            ),
        ],
    )

    style.map(
        "Garlic.Readonly.TEntry",
        fieldbackground=[
            (
                "readonly",
                GarlicTheme.INPUT_BACKGROUND,
            ),
        ],
        foreground=[
            (
                "readonly",
                GarlicTheme.INPUT_FOREGROUND,
            ),
        ],
    )
