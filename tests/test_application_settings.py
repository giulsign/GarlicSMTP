# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from garlicsmtp.configuration import (
    ApplicationSettings,
)


def test_default_settings():

    settings = ApplicationSettings()

    assert settings.hostname == "garlicsmtp.local"

    assert settings.smtp.host == "127.0.0.1"
    assert settings.smtp.port == 2525

    assert settings.imap.port == 1143

    assert settings.tor.enabled is True


def test_settings_instances_are_independent():

    first = ApplicationSettings()
    second = ApplicationSettings()

    first.smtp.port = 9999

    assert second.smtp.port == 2525
