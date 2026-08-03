from dataclasses import dataclass
from enum import Enum


class TorReplySeparator(Enum):

    FINAL = " "
    CONTINUATION = "-"
    DATA = "+"


@dataclass(
    frozen=True,
    slots=True,
)
class TorReplyLine:

    status: int
    separator: TorReplySeparator
    text: str
    data: tuple[str, ...] = ()

    @property
    def is_final(
        self,
    ) -> bool:
        return (
            self.separator
            is TorReplySeparator.FINAL
        )

    @property
    def is_continuation(
        self,
    ) -> bool:
        return (
            self.separator
            is TorReplySeparator.CONTINUATION
        )

    @property
    def has_data(
        self,
    ) -> bool:
        return (
            self.separator
            is TorReplySeparator.DATA
        )

    @property
    def data_text(
        self,
    ) -> str:
        return "\n".join(
            self.data
        )

    @property
    def keyword(
        self,
    ) -> str | None:
        if not self.text:
            return None

        head = self.text.split(
            " ",
            1,
        )[0]

        return head.split(
            "=",
            1,
        )[0]

    @property
    def value(
        self,
    ) -> str:
        if "=" in self.text:
            key_part, value_part = (
                self.text.split(
                    "=",
                    1,
                )
            )

            if " " not in key_part:
                return value_part

        if " " in self.text:
            return self.text.split(
                " ",
                1,
            )[1]

        return ""


@dataclass(
    frozen=True,
    slots=True,
)
class TorReply:

    status: int
    lines: tuple[TorReplyLine, ...]

    @property
    def successful(
        self,
    ) -> bool:
        return 200 <= self.status < 300

    @property
    def asynchronous(
        self,
    ) -> bool:
        return 600 <= self.status < 700

    @property
    def final_line(
        self,
    ) -> TorReplyLine:
        return self.lines[-1]

    @property
    def message(
        self,
    ) -> str:
        return self.final_line.text

    def find(
        self,
        keyword: str,
    ) -> TorReplyLine | None:
        normalized = keyword.upper()

        for line in self.lines:
            if (
                line.keyword is not None
                and line.keyword.upper()
                == normalized
            ):
                return line

        return None

    def find_all(
        self,
        keyword: str,
    ) -> tuple[TorReplyLine, ...]:
        normalized = keyword.upper()

        return tuple(
            line
            for line in self.lines
            if (
                line.keyword is not None
                and line.keyword.upper()
                == normalized
            )
        )
