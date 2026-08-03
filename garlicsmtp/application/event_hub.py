import threading
from collections.abc import Callable


ApplicationEventListener = Callable[
    [],
    None,
]


class ApplicationEventHub:

    def __init__(
        self,
    ) -> None:
        self._listeners: list[
            ApplicationEventListener
        ] = []

        self._lock = threading.RLock()

    def subscribe(
        self,
        listener: ApplicationEventListener,
    ) -> None:
        with self._lock:
            if listener not in self._listeners:
                self._listeners.append(
                    listener
                )

    def unsubscribe(
        self,
        listener: ApplicationEventListener,
    ) -> None:
        with self._lock:
            if listener in self._listeners:
                self._listeners.remove(
                    listener
                )

    def publish(
        self,
    ) -> None:
        with self._lock:
            listeners = tuple(
                self._listeners
            )

        for listener in listeners:
            listener()
