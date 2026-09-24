# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import tkinter as tk
from tkinter import ttk
from datetime import UTC, datetime
import threading

from garlicsmtp.application.view_model import (
    ApplicationViewModel,
)
from garlicsmtp.gui.tk_main_window import (
    MainWindow,
)
from tests.support import (
    FakeController,
    make_application_status,
    make_tor_status,
)
from garlicsmtp.application.compose_view_model import (
    ComposeViewModel,
)
from garlicsmtp.application import (
    MailboxSummary,
    MessageListViewModel,
    MessagePreviewViewModel,
    MessageSummary,
)
from garlicsmtp.models import (
    Envelope,
    MailHeaders,
    MailMessage,
)
from garlicsmtp.storage.entry import (
    MessageEntry,
)
from garlicsmtp.application.status import (
    RuntimeState,
)

def make_preview_entry():
    headers = MailHeaders()

    headers.add(
        "From",
        "Alice <alice@test.onion>",
    )
    headers.add(
        "Subject",
        "GarlicSMTP Preview",
    )

    return MessageEntry(
        id="message-1",
        mailbox="bob@test.onion",
        uid=12,
        message=MailMessage(
            envelope=Envelope(
                sender="alice@test.onion",
                recipients=[
                    "bob@test.onion",
                ],
            ),
            headers=headers,
            body="Hello from GarlicSMTP",
        ),
        internal_date=datetime(
            2026,
            8,
            7,
            9,
            30,
            tzinfo=UTC,
        ),
        flags={
            "\\Seen",
            "\\Flagged",
        },
    )

class FakeMessageExplorer:

    def list_messages(
        self,
        mailbox,
    ):
        if mailbox != "bob@test.onion":
            return ()

        return (
            MessageSummary(
                id="message-1",
                uid=1,
                sender="alice@test.onion",
                subject="GarlicSMTP message",
                internal_date=datetime(
                    2026,
                    8,
                    6,
                    10,
                    30,
                    tzinfo=UTC,
                ),
                size=128,
                flags=(),
            ),
        )

    def get_message(
        self,
        mailbox,
        message_id,
    ):
        if (
            mailbox == "bob@test.onion"
            and message_id == "message-1"
        ):
            return make_preview_entry()

        return None


def test_tk_main_window_builds_dashboard_sections():
    root = tk.Tk()
    root.withdraw()

    try:
        window = MainWindow(
            root,
            ApplicationViewModel(
                FakeController()
            ),
        )

        assert (
            window.application_section
            is not None
        )
        assert (
            window.services_section
            is not None
        )
        assert (
            window.tor_section
            is not None
        )
        assert (
            window.mailbox_section
            is not None
        )
        assert (
            window.mail_metrics_section
            is not None
        )
        assert (
            window.activity_section
            is not None
        )
        assert (
            window.message_list_section
            is not None
        )
        assert (
            window.message_preview_section
            is not None
        )

    finally:
        root.destroy()


def test_tk_main_window_has_no_compose_without_view_model():
    root = tk.Tk()
    root.withdraw()

    try:
        window = MainWindow(
            root,
            ApplicationViewModel(
                FakeController()
            ),
        )

        assert (
            window.compose_section
            is None
        )

    finally:
        root.destroy()


def test_tk_main_window_builds_compose_section():
    root = tk.Tk()
    root.withdraw()

    class FakeComposer:

        def send(
            self,
            *,
            sender,
            recipient,
            subject,
            body,
        ):
            del sender
            del recipient
            del subject
            del body
            return True

    try:
        compose = ComposeViewModel(
            FakeComposer()
        )

        window = MainWindow(
            root,
            ApplicationViewModel(
                FakeController(),
                compose=compose,
            ),
        )

        assert (
            window.compose_section
            is not None
        )
        assert (
            window.compose_section
            .view_model
            is compose
        )

    finally:
        root.destroy()


def test_tk_main_window_loads_selected_mailbox_messages():
    root = tk.Tk()
    root.withdraw()

    try:
        message_list = MessageListViewModel(
            FakeMessageExplorer()
        )

        view_model = ApplicationViewModel(
            FakeController(),
            message_list=message_list,
        )

        window = MainWindow(
            root,
            view_model,
        )

        assert (
            window.mailbox_section
            .select_mailbox(
                "bob@test.onion"
            )
            is True
        )

        assert (
            view_model.message_list
            .selected_mailbox
            == "bob@test.onion"
        )

        children = (
            window.message_list_section
            .table
            .get_children()
        )

        assert len(children) == 1

        assert (
            window.message_list_section
            .table
            .set(
                children[0],
                "subject",
            )
            == "GarlicSMTP message"
        )

    finally:
        root.destroy()


def test_tk_main_window_displays_selected_message_preview():
    root = tk.Tk()
    root.withdraw()

    try:
        explorer = FakeMessageExplorer()

        message_list = MessageListViewModel(
            explorer
        )

        message_preview = MessagePreviewViewModel(
            explorer
        )

        view_model = ApplicationViewModel(
            FakeController(),
            message_list=message_list,
            message_preview=message_preview,
        )

        window = MainWindow(
            root,
            view_model,
        )

        assert (
            window.mailbox_section
            .select_mailbox(
                "bob@test.onion"
            )
            is True
        )

        assert (
            window.message_list_section
            .select_message(
                "message-1"
            )
            is True
        )

        assert (
            view_model.message_preview.message_id
            == "message-1"
        )

        assert (
            view_model.message_preview.mailbox
            == "bob@test.onion"
        )

        assert (
            view_model.message_preview.subject
            == "GarlicSMTP Preview"
        )

        assert (
            window.message_preview_section
            .subject_value
            .get()
            == "GarlicSMTP Preview"
        )
    finally:
        root.destroy()


def test_tk_main_window_clears_preview_for_deleted_message():
    root = tk.Tk()
    root.withdraw()

    try:
        explorer = FakeMessageExplorer()

        message_list = MessageListViewModel(
            explorer
        )

        message_preview = MessagePreviewViewModel(
            explorer
        )

        view_model = ApplicationViewModel(
            FakeController(),
            message_list=message_list,
            message_preview=message_preview,
        )

        window = MainWindow(
            root,
            view_model,
        )

        assert (
            window.mailbox_section
            .select_mailbox(
                "bob@test.onion"
            )
            is True
        )

        assert (
            window.message_list_section
            .select_message(
                "message-1"
            )
            is True
        )

        assert (
            view_model.message_preview.message_id
            == "message-1"
        )

        window.message_list_section._notify_deleted(
            "message-1"
        )

        assert (
            view_model.message_preview.message_id
            is None
        )

        assert (
            view_model.message_preview.has_message
            is False
        )

    finally:
        root.destroy()


def test_tk_main_window_keeps_preview_for_other_deleted_message():
    root = tk.Tk()
    root.withdraw()

    try:
        explorer = FakeMessageExplorer()

        message_list = MessageListViewModel(
            explorer
        )

        message_preview = MessagePreviewViewModel(
            explorer
        )

        view_model = ApplicationViewModel(
            FakeController(),
            message_list=message_list,
            message_preview=message_preview,
        )

        window = MainWindow(
            root,
            view_model,
        )

        assert (
            window.mailbox_section
            .select_mailbox(
                "bob@test.onion"
            )
            is True
        )

        assert (
            window.message_list_section
            .select_message(
                "message-1"
            )
            is True
        )

        window.message_list_section._notify_deleted(
            "other-message"
        )

        assert (
            view_model.message_preview.message_id
            == "message-1"
        )

        assert (
            view_model.message_preview.has_message
            is True
        )

        assert (
            view_model.message_preview.subject
            == "GarlicSMTP Preview"
        )

    finally:
        root.destroy()


def test_tk_main_window_refreshes_all_sections():
    root = tk.Tk()
    root.withdraw()

    try:
        window = MainWindow(
            root,
            ApplicationViewModel(
                FakeController()
            ),
        )

        refreshed = []

        sections = (
            window.application_section,
            window.services_section,
            window.tor_section,
            window.mailbox_section,
            window.mail_metrics_section,
            window.activity_section,
            window.message_list_section,
            window.message_preview_section,
        )

        for section in sections:
            section.refresh_view = (
                lambda section=section:
                refreshed.append(section)
            )

        window.refresh_view()

        assert refreshed == list(sections)

    finally:
        root.destroy()


def test_tk_main_window_refreshes_compose_when_present():
    root = tk.Tk()
    root.withdraw()

    class FakeComposer:

        def send(
            self,
            *,
            sender,
            recipient,
            subject,
            body,
        ):
            del sender
            del recipient
            del subject
            del body
            return True

    try:
        compose = ComposeViewModel(
            FakeComposer()
        )

        view_model = ApplicationViewModel(
            FakeController(),
            compose=compose,
        )

        window = MainWindow(
            root,
            view_model,
        )

        refreshed = []

        window.compose_section.refresh_view = (
            lambda: refreshed.append(
                window.compose_section
            )
        )

        window.refresh_view()

        assert refreshed == [
            window.compose_section
        ]

    finally:
        root.destroy()


def test_tk_main_window_has_refresh_button():
    root = tk.Tk()
    root.withdraw()

    try:
        window = MainWindow(
            root,
            ApplicationViewModel(
                FakeController()
            ),
        )

        assert (
            window.refresh_button.cget("text")
            == "Refresh"
        )

    finally:
        root.destroy()


def test_tk_main_window_refresh_button_refreshes_view():
    root = tk.Tk()
    root.withdraw()

    try:
        window = MainWindow(
            root,
            ApplicationViewModel(
                FakeController()
            ),
        )

        refreshed = []

        window.refresh_view = (
            lambda: refreshed.append(True)
        )

        window.refresh_button.invoke()

        assert refreshed == [True]

    finally:
        root.destroy()


def test_tk_main_window_has_start_button():
    root = tk.Tk()
    root.withdraw()

    try:
        window = MainWindow(
            root,
            ApplicationViewModel(
                FakeController()
            ),
        )

        assert (
            window.start_button.cget("text")
            == "Start"
        )

    finally:
        root.destroy()


def test_tk_main_window_start_button_starts_and_refreshes():
    root = tk.Tk()
    root.withdraw()

    try:
        controller = FakeController()

        window = MainWindow(
            root,
            ApplicationViewModel(
                controller
            ),
        )

        started = []
        refreshed = []

        window.view_model.start = (
            lambda: started.append(True)
        )

        window.refresh_view = (
            lambda: refreshed.append(True)
        )

        window.start_button.invoke()

        assert started == [True]
        assert refreshed == [True]

    finally:
        root.destroy()


def test_tk_main_window_action_buttons_follow_stopped_state():
    root = tk.Tk()
    root.withdraw()

    try:
        window = MainWindow(
            root,
            ApplicationViewModel(
                FakeController(
                    RuntimeState.STOPPED
                )
            ),
        )

        assert (
            window.start_button.instate(
                ["!disabled"]
            )
        )
        assert (
            window.stop_button.instate(
                ["disabled"]
            )
        )
        assert (
            window.restart_button.instate(
                ["disabled"]
            )
        )

    finally:
        root.destroy()


def test_tk_main_window_stop_and_restart_buttons_execute_actions():
    root = tk.Tk()
    root.withdraw()

    try:
        controller = FakeController(
            RuntimeState.RUNNING
        )

        window = MainWindow(
            root,
            ApplicationViewModel(
                controller
            ),
        )

        assert (
            window.start_button.instate(
                ["disabled"]
            )
        )
        assert (
            window.stop_button.instate(
                ["!disabled"]
            )
        )
        assert (
            window.restart_button.instate(
                ["!disabled"]
            )
        )

        window.restart_button.invoke()

        assert controller.actions == [
            "restart"
        ]

        window.stop_button.invoke()

        assert controller.actions == [
            "restart",
            "stop",
        ]

        assert (
            window.start_button.instate(
                ["!disabled"]
            )
        )
        assert (
            window.stop_button.instate(
                ["disabled"]
            )
        )
        assert (
            window.restart_button.instate(
                ["disabled"]
            )
        )

    finally:
        root.destroy()


def test_tk_main_window_action_error_is_generic_and_refreshes(
    monkeypatch,
):
    root = tk.Tk()
    root.withdraw()

    try:
        window = MainWindow(
            root,
            ApplicationViewModel(
                FakeController()
            ),
        )

        dialogs = []
        refreshed = []

        def failing_action():
            raise RuntimeError(
                "SECRET "
                "hiddenservice.onion "
                "/private/garlicsmtp/key"
            )

        monkeypatch.setattr(
            window.view_model,
            "start",
            failing_action,
        )

        monkeypatch.setattr(
            "garlicsmtp.gui.tk_main_window.messagebox.showerror",
            lambda title, message, **kwargs: (
                dialogs.append(
                    (
                        title,
                        message,
                        kwargs,
                    )
                )
            ),
        )

        window.refresh_view = (
            lambda: refreshed.append(True)
        )

        window.start_button.invoke()

        assert len(dialogs) == 1

        title, message, kwargs = dialogs[0]

        assert title == "GarlicSMTP error"
        assert message == "Operation failed"

        displayed = f"{title} {message}"

        assert "SECRET" not in displayed
        assert ".onion" not in displayed
        assert "/private/" not in displayed

        assert kwargs["parent"] is root
        assert refreshed == [True]

    finally:
        root.destroy()


def test_tk_main_window_refresh_button_refreshes_view_model():
    root = tk.Tk()
    root.withdraw()

    try:
        window = MainWindow(
            root,
            ApplicationViewModel(
                FakeController()
            ),
        )

        actions = []
        refreshed = []

        window.view_model.refresh = (
            lambda: actions.append("refresh")
        )

        window.refresh_view = (
            lambda: refreshed.append(True)
        )

        window.refresh_button.invoke()

        assert actions == ["refresh"]
        assert refreshed == [True]

    finally:
        root.destroy()


def test_tk_main_window_places_top_dashboard_in_three_columns():
    root = tk.Tk()
    root.withdraw()

    try:
        window = MainWindow(
            root,
            ApplicationViewModel(
                FakeController()
            ),
        )

        assert (
            window.application_section.grid_info()
            ["row"]
            == 0
        )
        assert (
            window.application_section.grid_info()
            ["column"]
            == 0
        )

        assert (
            window.services_section.grid_info()
            ["row"]
            == 0
        )
        assert (
            window.services_section.grid_info()
            ["column"]
            == 1
        )

        assert (
            window.tor_section.grid_info()
            ["row"]
            == 0
        )
        assert (
            window.tor_section.grid_info()
            ["column"]
            == 2
        )

        assert (
            window.mailbox_section.grid_info()
            ["row"]
            == 1
        )
        assert (
            window.mailbox_section.grid_info()
            ["column"]
            == 0
        )

        assert (
            window.mail_metrics_section.grid_info()
            ["row"]
            == 1
        )
        assert (
            window.mail_metrics_section.grid_info()
            ["column"]
            == 1
        )

        assert (
            window.activity_section.grid_info()
            ["row"]
            == 1
        )
        assert (
            window.activity_section.grid_info()
            ["column"]
            == 2
        )

    finally:
        root.destroy()


def test_tk_main_window_places_compose_and_messages_layout():
    root = tk.Tk()
    root.withdraw()

    class FakeComposer:

        def send(
            self,
            *,
            sender,
            recipient,
            subject,
            body,
        ):
            del sender
            del recipient
            del subject
            del body
            return True

    try:
        compose = ComposeViewModel(
            FakeComposer()
        )

        window = MainWindow(
            root,
            ApplicationViewModel(
                FakeController(),
                compose=compose,
            ),
        )

        compose_info = (
            window.compose_section.grid_info()
        )

        assert compose_info["row"] == 2
        assert compose_info["column"] == 0
        assert compose_info["columnspan"] == 3

        assert isinstance(
            window.messages_pane,
            ttk.Frame,
        )

        pane_info = (
            window.messages_pane.grid_info()
        )

        assert pane_info["row"] == 3
        assert pane_info["column"] == 0
        assert pane_info["columnspan"] == 3

        assert (
            window.message_list_section.master
            is window.messages_pane
        )
        assert (
            window.message_preview_section.master
            is window.messages_pane
        )

        list_info = (
            window.message_list_section.grid_info()
        )
        preview_info = (
            window.message_preview_section.grid_info()
        )

        assert list_info["row"] == 0
        assert list_info["column"] == 0
        assert preview_info["row"] == 0
        assert preview_info["column"] == 1

    finally:
        root.destroy()


def test_tk_main_window_moves_messages_up_without_compose():
    root = tk.Tk()
    root.withdraw()

    try:
        window = MainWindow(
            root,
            ApplicationViewModel(
                FakeController()
            ),
        )

        assert window.compose_section is None

        pane_info = (
            window.messages_pane.grid_info()
        )

        assert pane_info["row"] == 2
        assert pane_info["column"] == 0
        assert pane_info["columnspan"] == 3

    finally:
        root.destroy()


def test_tk_main_window_dashboard_columns_and_messages_row_expand():
    root = tk.Tk()
    root.withdraw()

    try:
        window = MainWindow(
            root,
            ApplicationViewModel(
                FakeController()
            ),
        )

        for column in range(3):
            assert (
                window.content_frame.grid_columnconfigure(
                    column
                )["weight"]
                == 1
            )

        messages_row = int(
            window.messages_pane
            .grid_info()["row"]
        )

        assert (
            window.content_frame.grid_rowconfigure(
                messages_row
            )["weight"]
            == 1
        )

        assert (
            window.messages_pane.grid_columnconfigure(
                0
            )["weight"]
            == 1
        )
        assert (
            window.messages_pane.grid_columnconfigure(
                1
            )["weight"]
            == 2
        )
        assert (
            window.messages_pane.grid_rowconfigure(
                0
            )["weight"]
            == 1
        )

    finally:
        root.destroy()


def test_tk_main_window_dashboard_sections_belong_to_content_frame():
    root = tk.Tk()
    root.withdraw()

    try:
        window = MainWindow(
            root,
            ApplicationViewModel(
                FakeController()
            ),
        )

        assert isinstance(
            window.content_frame,
            ttk.Frame,
        )

        dashboard_sections = (
            window.application_section,
            window.services_section,
            window.tor_section,
            window.mailbox_section,
            window.mail_metrics_section,
            window.activity_section,
        )

        for section in dashboard_sections:
            assert section.master is window.content_frame

        assert (
            window.messages_pane.master
            is window.content_frame
        )
        assert (
            window.message_list_section.master
            is window.messages_pane
        )
        assert (
            window.message_preview_section.master
            is window.messages_pane
        )

    finally:
        root.destroy()


def test_tk_main_window_builds_header_and_action_bar():
    root = tk.Tk()
    root.withdraw()

    try:
        window = MainWindow(
            root,
            ApplicationViewModel(
                FakeController()
            ),
        )

        assert (
            window.title_label.cget("text")
            == "GarlicSMTP"
        )

        assert (
            window.subtitle_label.cget("text")
            == "Private mail infrastructure monitor"
        )

        assert (
            window.header_frame.grid_info()
            ["row"]
            == 0
        )

        assert (
            window.content_container.grid_info()
            ["row"]
            == 1
        )
        assert (
            window.content_canvas.master
            is window.content_container
        )
        assert (
            window.content_frame.master
            is window.content_canvas
        )

        assert (
            window.action_frame.grid_info()
            ["row"]
            == 2
        )

        assert (
            window.start_button.master
            is window.action_frame
        )
        assert (
            window.stop_button.master
            is window.action_frame
        )
        assert (
            window.restart_button.master
            is window.action_frame
        )
        assert (
            window.refresh_button.master
            is window.action_frame
        )

        assert (
            window.runtime_badge.get()
            == window.view_model.runtime_text
        )

    finally:
        root.destroy()


def test_tk_main_window_queues_view_model_event_from_worker_thread():
    root = tk.Tk()
    root.withdraw()

    try:
        view_model = ApplicationViewModel(
            FakeController()
        )

        window = MainWindow(
            root,
            view_model,
        )

        refresh_calls = []

        window.refresh_view = (
            lambda: refresh_calls.append(
                threading.get_ident()
            )
        )

        listener = view_model._listeners[-1]

        worker = threading.Thread(
            target=listener,
        )
        worker.start()
        worker.join()

        assert refresh_calls == []

        window._process_pending_refreshes()

        assert refresh_calls == [
            threading.get_ident()
        ]

    finally:
        root.destroy()


def test_tk_main_window_schedules_refresh_queue_poll():
    root = tk.Tk()
    root.withdraw()

    try:
        window = MainWindow(
            root,
            ApplicationViewModel(
                FakeController()
            ),
        )

        assert (
            window._refresh_poll_after_id
            is not None
        )

        scheduled = root.tk.call(
            "after",
            "info",
        )

        assert (
            window._refresh_poll_after_id
            in scheduled
        )

    finally:
        root.destroy()


def test_tk_main_window_close_stops_polling_and_running_application():
    root = tk.Tk()
    root.withdraw()

    try:
        controller = FakeController(
            runtime_state=RuntimeState.RUNNING,
        )

        view_model = ApplicationViewModel(
            controller
        )

        window = MainWindow(
            root,
            view_model,
        )

        listener = window._queue_refresh
        after_id = (
            window._refresh_poll_after_id
        )

        assert listener in view_model._listeners
        assert after_id is not None

        window.close()

        assert listener not in view_model._listeners
        assert "stop" in controller.actions

        assert (
            window._refresh_poll_after_id
            is None
        )

        scheduled = root.tk.call(
            "after",
            "info",
        )

        assert after_id not in scheduled

    finally:
        root.destroy()


def test_tk_main_window_content_has_vertical_scrollbar():
    root = tk.Tk()
    root.withdraw()

    try:
        window = MainWindow(
            root,
            ApplicationViewModel(
                FakeController()
            ),
        )

        assert window.content_canvas is not None
        assert window.content_scrollbar is not None

        assert (
            str(
                window.content_scrollbar.cget(
                    "orient"
                )
            )
            == "vertical"
        )

        assert (
            str(
                window.content_canvas.cget(
                    "yscrollcommand"
                )
            )
            != ""
        )

    finally:
        root.destroy()


def test_tk_main_window_messages_are_visible_at_bottom_of_scroll():
    root = tk.Tk()
    root.geometry("980x720")

    try:
        window = MainWindow(
            root,
            ApplicationViewModel(
                FakeController()
            ),
        )
        window.pack(
            fill="both",
            expand=True,
        )

        root.update_idletasks()

        window.content_canvas.yview_moveto(1.0)
        root.update_idletasks()

        canvas_top = (
            window.content_canvas.winfo_rooty()
        )
        canvas_bottom = (
            canvas_top
            + window.content_canvas.winfo_height()
        )

        messages_top = (
            window.messages_pane.winfo_rooty()
        )
        messages_bottom = (
            messages_top
            + window.messages_pane.winfo_height()
        )

        assert messages_bottom > canvas_top
        assert messages_top < canvas_bottom

    finally:
        root.destroy()


def test_tk_main_window_messages_container_uses_grid_layout():
    root = tk.Tk()
    root.withdraw()

    try:
        window = MainWindow(
            root,
            ApplicationViewModel(
                FakeController()
            ),
        )

        assert (
            window.message_list_section.winfo_manager()
            == "grid"
        )

        assert (
            window.message_preview_section.winfo_manager()
            == "grid"
        )

    finally:
        root.destroy()


def test_tk_main_window_mouse_wheel_scrolls_content_on_linux():
    root = tk.Tk()
    root.geometry("980x720")

    try:
        window = MainWindow(
            root,
            ApplicationViewModel(
                FakeController()
            ),
        )
        window.pack(
            fill="both",
            expand=True,
        )

        root.update_idletasks()

        window.content_canvas.yview_moveto(0.0)
        root.update_idletasks()

        before = window.content_canvas.yview()

        window._on_mouse_wheel_down(None)
        root.update_idletasks()

        after = window.content_canvas.yview()

        assert after[0] > before[0]

    finally:
        root.destroy()


def test_tk_main_window_mouse_wheel_scrolls_over_content_widget():
    root = tk.Tk()
    root.geometry("980x720")

    try:
        window = MainWindow(
            root,
            ApplicationViewModel(
                FakeController()
            ),
        )
        window.pack(
            fill="both",
            expand=True,
        )

        root.update_idletasks()

        window.content_canvas.yview_moveto(0.0)
        root.update_idletasks()

        before = window.content_canvas.yview()

        window.application_section.event_generate(
            "<Button-5>"
        )
        root.update_idletasks()

        after = window.content_canvas.yview()

        assert after[0] > before[0]

    finally:
        root.destroy()


def test_tk_main_window_keeps_message_preview_visible_before_selection():
    root = tk.Tk()
    root.geometry("980x720")

    try:
        window = MainWindow(
            root,
            ApplicationViewModel(
                FakeController()
            ),
        )
        window.pack(
            fill="both",
            expand=True,
        )

        root.update_idletasks()

        assert (
            window.message_list_section
            .winfo_ismapped()
        )
        assert (
            window.message_preview_section
            .winfo_ismapped()
        )

        pane_width = (
            window.messages_pane.winfo_width()
        )

        preview_x = (
            window.message_preview_section
            .winfo_x()
        )
        preview_width = (
            window.message_preview_section
            .winfo_width()
        )

        assert preview_width > 1
        assert preview_x < pane_width
        assert (
            preview_x + preview_width
            <= pane_width
        )

    finally:
        root.destroy()