from garlicsmtp.application.context import (
    ApplicationContext,
)
from garlicsmtp.application.status import (
    ApplicationStatus,
)
from garlicsmtp.application.status_provider import (
    ApplicationStatusProvider,
)


class ApplicationController:

    def __init__(
        self,
        context: ApplicationContext,
    ) -> None:
        self.context = context
        self.status_provider = (
            ApplicationStatusProvider(
                context
            )
        )

    def start(
        self,
    ) -> ApplicationStatus:
        self.context.runtime.start()

        return self.status()

    def stop(
        self,
    ) -> ApplicationStatus:
        self.context.runtime.stop()

        return self.status()

    def restart(
        self,
    ) -> ApplicationStatus:
        self.context.runtime.stop()
        self.context.runtime.start()

        return self.status()

    def status(
        self,
    ) -> ApplicationStatus:
        return self.status_provider.snapshot()
