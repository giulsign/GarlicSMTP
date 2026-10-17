# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import pytest

from garlicsmtp.core.engine import Bootstrap, GarlicSMTP
from garlicsmtp.core.engine import GarlicSMTPConfig




def test_bootstrap_builds_application(
    tmp_path,
    dek,
):
    config = GarlicSMTPConfig(
        mailbox_db=str(tmp_path / "mailboxes.db"),
    )

    app = Bootstrap(
        config=config,
        dek=dek,
    ).build()

    assert isinstance(app, GarlicSMTP)
    assert app.runtime is not None


def test_bootstrap_uses_socks_configuration():

    config = GarlicSMTPConfig(
        socks_host="127.0.0.2",
        socks_port=9150,
    )

    bootstrap = Bootstrap(config)

    onion = bootstrap.build_onion_transport()

    assert onion.socks_client.connection.proxy_host == "127.0.0.2"
    assert onion.socks_client.connection.proxy_port == 9150


def test_bootstrap_rejects_missing_dek():
    with pytest.raises(
        ValueError,
        match="DEK",
    ):
        Bootstrap().build_context()