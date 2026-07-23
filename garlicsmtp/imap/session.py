from enum import Enum, auto


class IMAPSessionState(Enum):

    NOT_AUTHENTICATED = auto()

    AUTHENTICATED = auto()

    SELECTED = auto()

    LOGOUT = auto()


class IMAPSession:
    def __init__(
        self,
    ) -> None:
        self.state = (
            IMAPSessionState.NOT_AUTHENTICATED
        )
        self.username: str | None = None
        self.selected_mailbox: str | None = None
        self.selected_mailbox_read_only = False

    def authenticate(
        self,
        username: str,
    ) -> None:
        self.username = username
        self.state = (
            IMAPSessionState.AUTHENTICATED
        )

    def select(
        self,
        mailbox: str,
        *,
        read_only: bool = False,
    ) -> None:
        self.selected_mailbox = mailbox
        self.selected_mailbox_read_only = (
            read_only
        )
        self.state = (
            IMAPSessionState.SELECTED
        )

    def close_mailbox(
        self,
    ) -> None:
        if self.state is not (
            IMAPSessionState.SELECTED
        ):
            raise RuntimeError(
                "Mailbox not selected"
            )

        self.selected_mailbox = None
        self.selected_mailbox_read_only = False
        self.state = (
            IMAPSessionState.AUTHENTICATED
        )

    def logout(
        self,
    ) -> None:
        self.selected_mailbox = None
        self.selected_mailbox_read_only = False
        self.state = (
            IMAPSessionState.LOGOUT
        )