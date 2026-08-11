from dataclasses import dataclass
from datetime import datetime


@dataclass(
    frozen=True,
    slots=True,
)
class MessageSummary:

    id: str
    uid: int

    sender: str
    subject: str

    internal_date: datetime
    size: int

    flags: tuple[str, ...]

    def __post_init__(
        self,
    ) -> None:
        if not self.id:
            raise ValueError(
                "message id cannot be empty"
            )

        if self.uid <= 0:
            raise ValueError(
                "message uid must be positive"
            )

        if self.size < 0:
            raise ValueError(
                "message size cannot be negative"
            )

    @property
    def seen(
        self,
    ) -> bool:
        return "\\Seen" in self.flags

    @property
    def flagged(
        self,
    ) -> bool:
        return "\\Flagged" in self.flags

    @property
    def deleted(
        self,
    ) -> bool:
        return "\\Deleted" in self.flags

    @property
    def draft(
        self,
    ) -> bool:
        return "\\Draft" in self.flags
