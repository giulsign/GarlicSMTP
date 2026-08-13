from collections.abc import Callable

from garlicsmtp.application.message_explorer import (
    MessageExplorerService,
)
from garlicsmtp.application.message_summary import (
    MessageSummary,
)


MessageListListener = Callable[
    [],
    None,
]


class MessageListViewModel:

    def __init__(
        self,
        explorer: MessageExplorerService,
    ) -> None:
        self.explorer = explorer

        self._selected_mailbox: (
            str | None
        ) = None

        self._messages: tuple[
            MessageSummary,
            ...
        ] = ()

        self._selected_message_id: (
            str | None
        ) = None

        self._listeners: list[
            MessageListListener
        ] = []

    @property
    def selected_mailbox(
        self,
    ) -> str | None:
        return self._selected_mailbox

    @property
    def messages(
        self,
    ) -> tuple[
        MessageSummary,
        ...
    ]:
        return self._messages

    @property
    def selected_message_id(
        self,
    ) -> str | None:
        return self._selected_message_id

    @property
    def selected_message(
        self,
    ) -> MessageSummary | None:
        if self._selected_message_id is None:
            return None

        for message in self._messages:
            if (
                message.id
                == self._selected_message_id
            ):
                return message

        return None

    @property
    def message_count(
        self,
    ) -> int:
        return len(
            self._messages
        )

    @property
    def message_count_text(
        self,
    ) -> str:
        if self._selected_mailbox is None:
            return "No mailbox selected"

        if self.message_count == 0:
            return "No messages"

        if self.message_count == 1:
            return "1 message"

        return (
            f"{self.message_count} messages"
        )

    @property
    def empty(
        self,
    ) -> bool:
        return not self._messages

    def subscribe(
        self,
        listener: MessageListListener,
    ) -> None:
        if listener not in self._listeners:
            self._listeners.append(
                listener
            )

    def unsubscribe(
        self,
        listener: MessageListListener,
    ) -> None:
        if listener in self._listeners:
            self._listeners.remove(
                listener
            )

    def select_mailbox(
        self,
        mailbox: str | None,
    ) -> None:
        normalized = self._normalize_mailbox(
            mailbox
        )

        mailbox_changed = (
            normalized
            != self._selected_mailbox
        )

        self._selected_mailbox = normalized

        if mailbox_changed:
            self._selected_message_id = None

        self.refresh()

    def select_message(
        self,
        message_id: str | None,
    ) -> bool:
        normalized = self._normalize_message_id(
            message_id
        )

        if normalized is None:
            changed = (
                self._selected_message_id
                is not None
            )

            self._selected_message_id = None

            if changed:
                self._notify()

            return True

        if not any(
            message.id == normalized
            for message in self._messages
        ):
            return False

        if (
            normalized
            == self._selected_message_id
        ):
            return True

        self._selected_message_id = (
            normalized
        )

        self._notify()

        return True

    def refresh(
        self,
    ) -> None:
        previous_messages = self._messages
        previous_selection = (
            self._selected_message_id
        )

        if self._selected_mailbox is None:
            current_messages = ()
        else:
            current_messages = (
                self.explorer.list_messages(
                    self._selected_mailbox
                )
            )

        self._messages = current_messages

        if (
            self._selected_message_id
            is not None
            and not any(
                message.id
                == self._selected_message_id
                for message in self._messages
            )
        ):
            self._selected_message_id = None

        if (
            self._messages != previous_messages
            or self._selected_message_id
            != previous_selection
        ):
            self._notify()

    def clear_selection(
        self,
    ) -> None:
        self.select_message(
            None
        )

    def _notify(
        self,
    ) -> None:
        for listener in tuple(
            self._listeners
        ):
            listener()

    @staticmethod
    def _normalize_mailbox(
        mailbox: str | None,
    ) -> str | None:
        if mailbox is None:
            return None

        if not isinstance(
            mailbox,
            str,
        ):
            raise TypeError(
                "mailbox must be text"
            )

        normalized = mailbox.strip()

        if not normalized:
            return None

        return normalized

    @staticmethod
    def _normalize_message_id(
        message_id: str | None,
    ) -> str | None:
        if message_id is None:
            return None

        if not isinstance(
            message_id,
            str,
        ):
            raise TypeError(
                "message id must be text"
            )

        normalized = (
            message_id.strip()
        )

        if not normalized:
            return None

        return normalized

    def mark_selected_read(
        self,
    ) -> bool:
        if (
            self._selected_mailbox is None
            or self._selected_message_id is None
        ):
            return False

        return self.explorer.mark_read(
            self._selected_mailbox,
            self._selected_message_id,
        )

    def mark_selected_unread(
        self,
    ) -> bool:
        if (
            self._selected_mailbox is None
            or self._selected_message_id is None
        ):
            return False

        return self.explorer.mark_unread(
            self._selected_mailbox,
            self._selected_message_id,
        )

    def delete_selected(
        self,
    ) -> bool:
        if (
            self._selected_mailbox is None
            or self._selected_message_id is None
        ):
            return False

        deleted = self.explorer.delete_message(
            self._selected_mailbox,
            self._selected_message_id,
        )

        if not deleted:
            return False

        self.refresh()

        return True
