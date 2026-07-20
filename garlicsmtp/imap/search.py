from dataclasses import dataclass

from garlicsmtp.storage.entry import MessageEntry


class IMAPSearchError(ValueError):
    pass


@dataclass(slots=True)
class IMAPSearchEngine:

    entries: list[MessageEntry]

    FLAG_CRITERIA = {
        "ALL",
        "SEEN",
        "UNSEEN",
        "FLAGGED",
        "UNFLAGGED",
    }

    VALUE_CRITERIA = {
        "FROM",
        "TO",
        "SUBJECT",
        "TEXT",
    }

    def search(
        self,
        criteria: list[str],
    ) -> list[int]:
        if not criteria:
            raise IMAPSearchError(
                "SEARCH requires criteria"
            )

        predicates = self._parse_criteria(
            criteria
        )

        return [
            entry.uid
            for entry in self.entries
            if all(
                predicate(entry)
                for predicate in predicates
            )
        ]

    def _parse_criteria(
        self,
        criteria: list[str],
    ):
        predicates = []
        index = 0

        while index < len(criteria):
            criterion = criteria[index].upper()

            if criterion in self.FLAG_CRITERIA:
                predicates.append(
                    self._build_flag_predicate(
                        criterion
                    )
                )

                index += 1
                continue

            if criterion in self.VALUE_CRITERIA:
                if index + 1 >= len(criteria):
                    raise IMAPSearchError(
                        f"{criterion} requires a value"
                    )

                value = self._normalize_value(
                    criteria[index + 1]
                )

                predicates.append(
                    self._build_value_predicate(
                        criterion,
                        value,
                    )
                )

                index += 2
                continue

            raise IMAPSearchError(
                "Unsupported SEARCH criterion "
                f"{criterion}"
            )

        return predicates

    def _build_flag_predicate(
        self,
        criterion: str,
    ):
        handlers = {
            "ALL": self._match_all,
            "SEEN": self._match_seen,
            "UNSEEN": self._match_unseen,
            "FLAGGED": self._match_flagged,
            "UNFLAGGED": self._match_unflagged,
        }

        return handlers[criterion]

    def _build_value_predicate(
        self,
        criterion: str,
        value: str,
    ):
        if criterion == "FROM":
            return lambda entry: self._contains(
                entry.message.envelope.sender,
                value,
            )

        if criterion == "TO":
            return lambda entry: any(
                self._contains(
                    recipient,
                    value,
                )
                for recipient
                in entry.message.envelope.recipients
            )

        if criterion == "SUBJECT":
            return lambda entry: self._contains(
                str(
                    entry.message.headers.fields.get(
                        "Subject",
                        "",
                    )
                ),
                value,
            )

        if criterion == "TEXT":
            return lambda entry: (
                self._contains(
                    entry.message.envelope.sender,
                    value,
                )
                or any(
                    self._contains(
                        recipient,
                        value,
                    )
                    for recipient
                    in entry.message.envelope.recipients
                )
                or self._headers_contain(
                    entry,
                    value,
                )
                or self._contains(
                    entry.message.body or "",
                    value,
                )
            )

        raise IMAPSearchError(
            "Unsupported SEARCH criterion "
            f"{criterion}"
        )

    @staticmethod
    def _normalize_value(
        value: str,
    ) -> str:
        return value.strip('"')

    @staticmethod
    def _contains(
        source: str,
        value: str,
    ) -> bool:
        return (
            value.casefold()
            in source.casefold()
        )

    def _headers_contain(
        self,
        entry: MessageEntry,
        value: str,
    ) -> bool:
        for name, header_value in (
            entry.message.headers.fields.items()
        ):
            if self._contains(
                name,
                value,
            ):
                return True

            if isinstance(
                header_value,
                list,
            ):
                if any(
                    self._contains(
                        str(item),
                        value,
                    )
                    for item in header_value
                ):
                    return True

            elif self._contains(
                str(header_value),
                value,
            ):
                return True

        return False

    @staticmethod
    def _match_all(
        entry: MessageEntry,
    ) -> bool:
        return True

    @staticmethod
    def _match_seen(
        entry: MessageEntry,
    ) -> bool:
        return "\\Seen" in entry.flags

    @staticmethod
    def _match_unseen(
        entry: MessageEntry,
    ) -> bool:
        return "\\Seen" not in entry.flags

    @staticmethod
    def _match_flagged(
        entry: MessageEntry,
    ) -> bool:
        return "\\Flagged" in entry.flags

    @staticmethod
    def _match_unflagged(
        entry: MessageEntry,
    ) -> bool:
        return "\\Flagged" not in entry.flags