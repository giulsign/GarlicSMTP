# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.logger import Logger


def test_logger_info(capsys):

    logger = Logger()

    logger.info("hello")

    captured = capsys.readouterr()

    assert captured.out == "hello\n"