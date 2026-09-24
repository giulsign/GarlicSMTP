# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import sys
import tkinter as tk

from garlicsmtp.application import (
    ApplicationBuilder,
    ApplicationController,
    ApplicationViewModel,
)
from garlicsmtp.gui.tk_main_window import (
    MainWindow,
)
from garlicsmtp.application import (
    ApplicationBuilder,
    ApplicationController,
    ApplicationViewModel,
    MessageExplorerService,
    MessageListViewModel,
)
from garlicsmtp.application import (
    ApplicationBuilder,
    ApplicationController,
    ApplicationViewModel,
    MessageExplorerService,
    MessageListViewModel,
    MessagePreviewViewModel,
)
from garlicsmtp.application import (
    ComposeViewModel,
    MailComposerService,
)
from garlicsmtp.configuration import (
    ApplicationPaths,
)


def build_view_model(
    *,
    paths=None,
) -> ApplicationViewModel:
    context = ApplicationBuilder(
        paths=paths,
    ).build()

    controller = ApplicationController(
        context
    )

    message_explorer = (
        MessageExplorerService(
            context.store
        )
    )

    message_list = MessageListViewModel(
        message_explorer
    )

    message_preview = (
        MessagePreviewViewModel(
            message_explorer
        )
    )

    mail_composer = MailComposerService(
        context.pipeline,
        signer=context.signer,
        verifier=getattr(
            context,
            "verifier",
            None,
        ),
    )

    compose = ComposeViewModel(
        mail_composer
    )

    return ApplicationViewModel(
        controller,
        message_list=message_list,
        message_preview=message_preview,
        compose=compose,
    )


def run_gui(
    argv: list[str] | None = None,
    *,
    paths=None,
) -> int:
    root = tk.Tk()

    root.title(
        "GarlicSMTP Monitor"
    )

    root.geometry(
        "980x720"
    )

    view_model = build_view_model(
        paths=(
            paths
            if paths is not None
            else ApplicationPaths.for_user()
        ),
    )

    window = MainWindow(
        root,
        view_model,
    )

    window.pack(
        fill="both",
        expand=True,
    )

    def close_window() -> None:
        window.close()
        root.destroy()

    root.protocol(
        "WM_DELETE_WINDOW",
        close_window,
    )

    root.mainloop()

    return 0


def main() -> int:
    return run_gui()

if __name__ == "__main__":
    raise SystemExit(
        main()
    )
