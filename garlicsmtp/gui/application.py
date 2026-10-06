# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import sys
import tkinter as tk
from tkinter import messagebox

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
from garlicsmtp.storage.store import (
    MessageStore,
)
from garlicsmtp.storage.sqlite.backend import (
    SQLiteMessageStoreBackend,
)
from garlicsmtp.storage.attachment_store import (
    AttachmentStore,
)
from garlicsmtp.gui.folder_opener import (
    FolderOpener,
    open_directory,
)
from garlicsmtp.security.auth.account_credentials import (
    AccountCredentialStore,
)
from garlicsmtp.gui.tk_authentication import (
    prompt_login,
    prompt_setup,
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

    received_message_explorer = MessageExplorerService(
        context.store
    )

    sent_store = MessageStore(
        backend=SQLiteMessageStoreBackend(
            context.paths.sent_mailbox_database
        ),
        attachment_store=AttachmentStore(
            context.paths.attachments_dir
        ),
    )

    sent_message_explorer = MessageExplorerService(
        sent_store
    )

    received_message_list = MessageListViewModel(
        received_message_explorer
    )
    received_message_preview = MessagePreviewViewModel(
        received_message_explorer
    )

    sent_message_list = MessageListViewModel(
        sent_message_explorer
    )
    sent_message_preview = MessagePreviewViewModel(
        sent_message_explorer
    )

    mail_composer = MailComposerService(
        context.pipeline,
        signer=context.signer,
        verifier=getattr(
            context,
            "verifier",
            None,
        ),
        sent_store=sent_store,
    )

    compose = ComposeViewModel(
        mail_composer
    )

    return ApplicationViewModel(
        controller,
        received_message_list=received_message_list,
        received_message_preview=received_message_preview,
        sent_message_list=sent_message_list,
        sent_message_preview=sent_message_preview,
        compose=compose,
        sent_store=sent_store,
    )


def authenticate_application(
    *,
    paths,
    prompt,
    setup_prompt=None,
    invalid_credentials=None,
    invalid_setup=None,
) -> bool:
    store = AccountCredentialStore(
        path=paths.account_credentials_file,
    )

    if not paths.account_credentials_file.exists():
        while True:
            credentials = setup_prompt()

            if credentials is None:
                return False

            username, password, password_confirmation = credentials

            if password != password_confirmation:
                if invalid_setup is not None:
                    invalid_setup(
                        "Passwords do not match"
                    )
                continue

            try:
                store.create(
                    username=username,
                    password=password,
                )
            except ValueError as exc:
                if invalid_setup is not None:
                    invalid_setup(
                        str(exc)
                    )
                continue

            return True

    while True:
        credentials = prompt()

        if credentials is None:
            return False

        username, password = credentials

        if store.authenticate(
            username=username,
            password=password,
        ):
            return True

        if invalid_credentials is not None:
            invalid_credentials()


def run_gui(
    argv: list[str] | None = None,
    *,
    paths=None,
    authenticate=None,
) -> int:
    root = tk.Tk()

    root.title(
        "GarlicSMTP Monitor"
    )

    root.geometry(
        "980x720"
    )

    root.withdraw()

    application_paths = (
        paths
        if paths is not None
        else ApplicationPaths.for_user()
    )

    if authenticate is None:
        authenticated = authenticate_application(
            paths=application_paths,
            prompt=lambda: prompt_login(root),
            setup_prompt=lambda: prompt_setup(root),
            invalid_credentials=lambda: messagebox.showerror(
                "GarlicSMTP login",
                "Invalid username or password",
                parent=root,
            ),
            invalid_setup=lambda message: messagebox.showerror(
                "GarlicSMTP account setup",
                message,
                parent=root,
            ),
        )
    else:
        authenticated = authenticate(
            paths=application_paths,
        )

    if not authenticated:
        root.destroy()
        return 1

    root.deiconify()

    view_model = build_view_model(
        paths=application_paths,
    )

    folder_opener = FolderOpener(
        open_directory=open_directory
    )

    window = MainWindow(
        root,
        view_model,
        folder_opener=folder_opener,
        attachment_directory_factory=(
            lambda message_id: (
                application_paths.cache_dir
                / "attachments"
                / message_id
            )
        ),
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
