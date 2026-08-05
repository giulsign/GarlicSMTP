from dataclasses import dataclass

from garlicsmtp.application.mailbox_summary import (
    MailboxSummary,
)


@dataclass(
    frozen=True,
    slots=True,
)
class MailboxItemViewModel:

    address: str
    message_count: int

    @property
    def message_count_text(
        self,
    ) -> str:
        if self.message_count == 1:
            return "1 message"

        return (
            f"{self.message_count} messages"
        )

    @property
    def display_text(
        self,
    ) -> str:
        return (
            f"{self.address}  —  "
            f"{self.message_count_text}"
        )

    @classmethod
    def from_summary(
        cls,
        summary: MailboxSummary,
    ) -> "MailboxItemViewModel":
        return cls(
            address=summary.address,
            message_count=(
                summary.message_count
            ),
        )
