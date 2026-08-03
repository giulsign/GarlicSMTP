import sys

from PySide6.QtWidgets import (
    QApplication,
)

from garlicsmtp.application import (
    ApplicationBuilder,
    ApplicationController,
    ApplicationViewModel,
)
from garlicsmtp.gui.main_window import (
    MainWindow,
)


def build_view_model(
) -> ApplicationViewModel:
    context = ApplicationBuilder().build()

    controller = ApplicationController(
        context
    )

    return ApplicationViewModel(
        controller
    )


def run_gui(
    argv: list[str] | None = None,
) -> int:
    arguments = (
        argv
        if argv is not None
        else sys.argv
    )

    application = QApplication(
        arguments
    )

    application.setApplicationName(
        "GarlicSMTP"
    )

    view_model = build_view_model()

    window = MainWindow(
        view_model
    )

    window.show()

    return application.exec()


def main() -> int:
    return run_gui()

if __name__ == "__main__":
    raise SystemExit(
        main()
    )
