# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import logging
from pathlib import Path

"""
_logger = None


def get_logger(config):

    global _logger

    if _logger is not None:
        return _logger

    logdir = Path(config.get("logging", "directory"))
    logfile = config.get("logging", "file")

    logdir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("GarlicSMTP")
    logger.setLevel(config.get("general", "loglevel"))

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)-8s %(message)s"
    )

    fh = logging.FileHandler(logdir / logfile)
    fh.setFormatter(formatter)

    sh = logging.StreamHandler()
    sh.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(sh)

    _logger = logger

    return logger"""

class Logger:

    def info(self, message: str) -> None:
        print(message)

    def warning(self, message: str) -> None:
        print(message)

    def error(self, message: str) -> None:
        print(message)
