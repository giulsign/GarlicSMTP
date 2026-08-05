from dataclasses import dataclass


@dataclass(
    frozen=True,
    slots=True,
)
class MailboxSummary:

    address: str
    message_count: int

    def __post_init__(
        self,
    ) -> None:
        if not self.address:
            raise ValueError(
                "mailbox address cannot be empty"
            )

        if self.message_count < 0:
            raise ValueError(
                "message_count cannot be negative"
            )
