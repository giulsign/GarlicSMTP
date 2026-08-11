from garlicsmtp.application import (
    MessageListViewModel,
)
from garlicsmtp.gui.application import (
    build_view_model,
)


def test_gui_builds_message_list_view_model(
    tmp_path,
    monkeypatch,
):
    view_model = build_view_model()

    assert isinstance(
        view_model.message_list,
        MessageListViewModel,
    )
