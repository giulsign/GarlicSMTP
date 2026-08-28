# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.imap.idle import IMAPIdleSession


def test_idle_session_starts_inactive():
    idle = IMAPIdleSession()

    assert idle.active is False
    assert idle.should_accept_command() is True


def test_idle_session_enters_idle():
    idle = IMAPIdleSession()

    idle.enter("A001")

    assert idle.active is True
    assert idle.should_accept_command() is False


def test_idle_session_exits_idle():
    idle = IMAPIdleSession()
    idle.enter("A001")

    tag = idle.exit()

    assert tag == "A001"
    assert idle.active is False
    assert idle.should_accept_command() is True


def test_idle_session_handles_done():
    idle = IMAPIdleSession()
    idle.enter("A001")

    tag = idle.handle_input("DONE")

    assert tag == "A001"
    assert idle.active is False


def test_idle_session_handles_done_case_insensitively():
    idle = IMAPIdleSession()
    idle.enter("A001")

    tag = idle.handle_input(" done ")

    assert tag == "A001"
    assert idle.active is False


def test_idle_session_ignores_other_input_during_idle():
    idle = IMAPIdleSession()
    idle.enter("A001")

    tag = idle.handle_input("A002 NOOP")

    assert tag == ""
    assert idle.active is True


def test_idle_session_does_not_handle_input_when_inactive():
    idle = IMAPIdleSession()

    tag = idle.handle_input("DONE")

    assert tag is None


def test_idle_session_returns_pending_notifications():
    idle = IMAPIdleSession()

    idle.notify("* 1 EXISTS")
    idle.notify("* 2 EXISTS")

    notifications = idle.drain_notifications()

    assert notifications == (
        "* 1 EXISTS",
        "* 2 EXISTS",
    )

def test_idle_session_clears_returned_notifications():
    idle = IMAPIdleSession()

    idle.notify("* 1 EXISTS")

    idle.drain_notifications()

    assert idle.drain_notifications() == ()


def test_idle_session_has_no_notifications_initially():
    idle = IMAPIdleSession()

    assert idle.has_notifications() is False


def test_idle_session_reports_pending_notifications():
    idle = IMAPIdleSession()

    idle.notify("* 1 EXISTS")

    assert idle.has_notifications() is True

    idle.drain_notifications()

    assert idle.has_notifications() is False


def test_idle_session_formats_exists_notification():
    idle = IMAPIdleSession()

    idle.notify_exists(3)

    assert idle.drain_notifications() == (
        "* 3 EXISTS",
    )


def test_idle_session_formats_expunge_notification():
    idle = IMAPIdleSession()

    idle.notify_expunge(7)

    assert idle.drain_notifications() == (
        "* 7 EXPUNGE",
    )


def test_idle_session_notifies_generic_response():
    idle = IMAPIdleSession()

    idle.notify_response(
        "* OK Still here"
    )

    assert idle.drain_notifications() == (
        "* OK Still here",
    )


def test_idle_session_notifies_mailbox_changed():
    idle = IMAPIdleSession()

    idle.notify_mailbox_changed(5)

    assert idle.drain_notifications() == (
        "* 5 EXISTS",
    )