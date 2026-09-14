import tomllib
from pathlib import Path


def test_pyproject_exposes_cli_and_gui_entry_points():
    pyproject_path = (
        Path(__file__).resolve().parents[1]
        / "pyproject.toml"
    )

    with pyproject_path.open(
        "rb",
    ) as file:
        metadata = tomllib.load(file)

    assert metadata["project"]["scripts"] == {
        "garlicsmtp": "garlicsmtp.cli:main",
    }

    assert metadata["project"]["gui-scripts"] == {
        "garlicsmtp-gui": (
            "garlicsmtp.gui.application:main"
        ),
    }
