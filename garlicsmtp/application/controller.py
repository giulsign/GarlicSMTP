from garlicsmtp.application.context import (
    ApplicationContext,
)
from garlicsmtp.application.status import (
    ApplicationStatus,
)
from garlicsmtp.application.status_provider import (
    ApplicationStatusProvider,
)
from garlicsmtp.application.event import (
    ApplicationEventSource,
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

        self.context.event_service.info(
            ApplicationEventSource.APPLICATION,
            "Application started",
        )

        return self.status()


    def stop(
        self,
    ) -> ApplicationStatus:
        self.context.runtime.stop()

        self.context.event_service.info(
            ApplicationEventSource.APPLICATION,
            "Application stopped",
        )

        return self.status()


    def restart(
        self,
    ) -> ApplicationStatus:
        self.context.runtime.stop()
        self.context.runtime.start()

        self.context.event_service.info(
            ApplicationEventSource.APPLICATION,
            "Application restarted",
        )

        return self.status()

    def status(
        self,
    ) -> ApplicationStatus:
        return self.status_provider.snapshot()

    def subscribe(
        self,
        listener,
    ) -> None:
        self.context.event_hub.subscribe(
            listener
        )


    def unsubscribe(
        self,
        listener,
    ) -> None:
        self.context.event_hub.unsubscribe(
            listener
        )
