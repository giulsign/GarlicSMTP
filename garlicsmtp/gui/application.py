# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import sys
import tkinter as tk
from tkinter import font as tkfont
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
    RecoveryDialog,
    PasswordResetDialog,
    prompt_login,
    prompt_setup,
)
from garlicsmtp.security.at_rest_key_manager import (
    AtRestKeyManager,
)



def build_view_model(
    *,
    paths=None,
    dek: bytes,
) -> ApplicationViewModel:
    if not isinstance(dek, bytes) or len(dek) != 32:
        raise ValueError("DEK non valida o mancante")

    context = ApplicationBuilder(
        paths=paths,
        dek=dek,
    ).build()


    controller = ApplicationController(
        context
    )

    received_message_explorer = MessageExplorerService(
        context.store
    )

    sent_store = MessageStore(

        backend=SQLiteMessageStoreBackend(
            context.paths.sent_mailbox_database,
            dek=dek,
        ),

        attachment_store=AttachmentStore(
            context.paths.attachments_dir,
            dek=dek,
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

def setup_application_dek(
    *,
    paths,
    username: str,
    password: str,
    show_recovery,
) -> bytes:
    store = AccountCredentialStore(
        path=paths.account_credentials_file,
    )

    recovery_key = AtRestKeyManager().generate_recovery_key()

    store.create(
        username=username,
        password=password,
    )

    store.enable_recovery(
        username=username,
        password=password,
        recovery_key=recovery_key,
    )

    dek = store.unlock_dek_with_password(
        username=username,
        password=password,
    )

    entered_recovery_key = show_recovery(recovery_key)

    if not isinstance(entered_recovery_key, str) or not entered_recovery_key:
        raise ValueError(
            "Conferma della recovery obbligatoria"
        )

    store.confirm_recovery(
        username=username,
        recovery_key=entered_recovery_key,
    )

    return dek

def recover_application_password(
    *,
    paths,
    username: str,
    recovery_key: str,
    new_password: str,
    show_recovery,
) -> bool:
    new_recovery_key = AtRestKeyManager().generate_recovery_key()

    confirmed_key = show_recovery(new_recovery_key)

    if confirmed_key != new_recovery_key:
        return False

    store = AccountCredentialStore(
        path=paths.account_credentials_file,
    )

    store.reset_password_with_recovery(
        username=username,
        recovery_key=recovery_key,
        new_password=new_password,
        new_recovery_key=new_recovery_key,
    )

    return True

def unlock_application_dek(
    *,
    paths,
    prompt,
    invalid_credentials=None,
    show_recovery=None,
    on_forgot_password=None,
) -> bytes | None:
    store = AccountCredentialStore(
        path=paths.account_credentials_file,
    )

    while True:
        credentials = prompt()

        if credentials is None:
            return None

        if credentials == "forgot_password":
            if on_forgot_password is not None:
                on_forgot_password()
            continue

        username, password = credentials

        if not store.authenticate(
            username=username,
            password=password,
        ):
            if invalid_credentials is not None:
                invalid_credentials()
            continue


        try:
            dek = store.unlock_dek_with_password(
                username=username,
                password=password,
            )
        except ValueError as exc:
            raise ValueError(
                "DEK non configurata o non sbloccabile"
            ) from exc

        data = store._read_credentials()

        if data.get("recovery_confirmed") is not True:
            if show_recovery is None:
                raise ValueError(
                    "Conferma della recovery obbligatoria"
                )

            recovery_key = AtRestKeyManager().generate_recovery_key()

            store.replace_unconfirmed_recovery(
                username=username,
                password=password,
                new_recovery_key=recovery_key,
            )

            entered_recovery_key = show_recovery(recovery_key)

            if (
                not isinstance(entered_recovery_key, str)
                or not entered_recovery_key
            ):
                raise ValueError(
                    "Conferma della recovery obbligatoria"
                )

            store.confirm_recovery(
                username=username,
                recovery_key=entered_recovery_key,
            )

        return dek


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


def configure_application_fonts(
    root,
) -> None:
    for font_name in (
        "TkDefaultFont",
        "TkTextFont",
        "TkFixedFont",
        "TkMenuFont",
        "TkHeadingFont",
    ):
        font = tkfont.nametofont(
            font_name,
            root=root,
        )
        font.configure(
            size=font.cget("size") + 2,
        )           

def show_recovery_key(
    recovery_key: str,
    *,
    master,
) -> str | bool:
    dialog = RecoveryDialog(
        master,
        recovery_key,
    )
    dialog.grab_set()
    dialog.wait_window()
    return dialog.result

def prompt_password_reset(master):
    dialog = PasswordResetDialog(master)
    dialog.grab_set()
    dialog.wait_window()
    return dialog.result

def handle_forgot_password(*, paths, master) -> None:
    credentials = prompt_password_reset(master)

    if credentials is None:
        return

    username, recovery_key, new_password = credentials

    try:
        recovered = recover_application_password(
            paths=paths,
            username=username,
            recovery_key=recovery_key,
            new_password=new_password,
            show_recovery=lambda key: show_recovery_key(
                key,
                master=master,
            ),
        )
    except ValueError as exc:
        messagebox.showerror(
            "GarlicSMTP password recovery",
            str(exc),
            parent=master,
        )
        return

    if recovered:
        messagebox.showinfo(
            "GarlicSMTP password recovery",
            "Password reset completed. Sign in with your new password.",
            parent=master,
        )


def run_gui(
    argv: list[str] | None = None,
    *,
    paths=None,
    authenticate=None,
) -> int:
    root = tk.Tk()

    configure_application_fonts(
        root,
    )

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

    icon = tk.PhotoImage(
        file=str(
            application_paths.application_icon
        )
    )

    root.iconphoto(
        True,
        icon,
    )

    if authenticate is None:
        if application_paths.account_credentials_file.exists():
            try:
                authenticated = unlock_application_dek(
                    paths=application_paths,
                    prompt=lambda: prompt_login(root),
                    invalid_credentials=lambda: messagebox.showerror(
                        "GarlicSMTP login",
                        "Invalid username or password",
                        parent=root,
                    ),
                    show_recovery=lambda recovery_key: show_recovery_key(
                        recovery_key,
                        master=root,
                    ),
                    on_forgot_password=lambda: handle_forgot_password(
                        paths=application_paths,
                        master=root,
                    ),
                )
            except Exception:
                root.destroy()
                raise
        else:
            while True:
                credentials = prompt_setup(root)

                if credentials is None:
                    authenticated = None
                    break

                username, password, password_confirmation = credentials

                if password != password_confirmation:
                    messagebox.showerror(
                        "GarlicSMTP account setup",
                        "Passwords do not match",
                        parent=root,
                    )
                    continue

                try:
                    authenticated = setup_application_dek(
                        paths=application_paths,
                        username=username,
                        password=password,
                        show_recovery=lambda recovery_key: show_recovery_key(
                            recovery_key,
                            master=root,
                        ),
                    )
                except ValueError as exc:
                    messagebox.showerror(
                        "GarlicSMTP account setup",
                        str(exc),
                        parent=root,
                    )
                    authenticated = None

                    if application_paths.account_credentials_file.exists():
                        break

                    continue
                except Exception:
                    root.destroy()
                    raise

                break
    else:
        authenticated = authenticate(
            paths=application_paths,
        )


    if authenticated is False or authenticated is None:
        root.destroy()
        return 1

    if not isinstance(authenticated, bytes) or len(authenticated) != 32:
        root.destroy()
        raise ValueError("DEK non valida o mancante")

    dek = authenticated

    try:
        view_model = build_view_model(
            paths=application_paths,
            dek=dek,
        )
    except IsADirectoryError as exc:
        messagebox.showerror(
            "Onion HTML configuration error",
            (
                "The configured Onion HTML path points to a directory "
                "instead of a file.\n\n"
                f"{exc}\n\n"
                "Select a valid HTML file in the Onion page settings."
            ),
            parent=root,
        )
        root.destroy()
        return 1
    except Exception:
        root.destroy()
        raise

    root.deiconify()


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
        onion_settings_path=application_paths.settings_file,
    )

    window.pack(
        fill="both",
        expand=True,
    )

    def close_window() -> None:
        if not window.close():
            messagebox.showwarning(
                "GarlicSMTP",
                (
                    "A message is being sent. "
                    "Please wait for it to finish "
                    "before closing GarlicSMTP."
                ),
                parent=root,
            )
            return

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
