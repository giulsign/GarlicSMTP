# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.imap.command_result import (
    IMAPCommandAction,
    IMAPCommandResult,
)
from garlicsmtp.imap.reply import IMAPReply

from garlicsmtp.imap.command_result import (
    IMAPCommandResult,
)
from garlicsmtp.imap.protocol import IMAPProtocol




def test_imap_command_result_preserves_responses():
    responses = [
        IMAPReply.tagged(
            "A001",
            "OK",
            "Command completed",
        )
    ]

    result = IMAPCommandResult.complete(
        responses
    )

    assert result.as_list() == responses


def test_imap_command_result_defaults_to_complete():
    result = IMAPCommandResult.complete(
        []
    )

    assert result.action is (
        IMAPCommandAction.COMPLETE
    )


def test_imap_command_result_enter_idle():
    result = IMAPCommandResult.enter_idle(
        []
    )

    assert result.action is (
        IMAPCommandAction.ENTER_IDLE
    )

    assert result.as_list() == []


def test_execute_command_preserves_command_result():
    protocol = IMAPProtocol()

    expected = IMAPCommandResult.enter_idle(
        []
    )

    result = protocol._execute_command(
        expected,
    )

    assert result is expected

