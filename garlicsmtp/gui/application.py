# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import sys

from PySide6.QtWidgets import (
    QApplication,
)

from garlicsmtp.application import (
    ApplicationBuilder,
    ApplicationController,
    ApplicationViewModel,
)
from garlicsmtp.gui.main_window import (
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


def build_view_model(
) -> ApplicationViewModel:
    context = ApplicationBuilder().build()

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
) -> int:
    arguments = (
        argv
        if argv is not None
        else sys.argv
    )

    application = QApplication(
        arguments
    )

    application.setApplicationName(
        "GarlicSMTP"
    )

    view_model = build_view_model()

    window = MainWindow(
        view_model
    )

    window.show()

    return application.exec()


def main() -> int:
    return run_gui()

if __name__ == "__main__":
    raise SystemExit(
        main()
    )
