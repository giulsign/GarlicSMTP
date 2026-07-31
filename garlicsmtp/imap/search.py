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
        "DELETED",
        "UNDELETED",
        "ANSWERED",
        "UNANSWERED",
        "DRAFT",
        "UNDRAFT",
    }

    VALUE_CRITERIA = {
        "FROM",
        "TO",
        "SUBJECT",
        "TEXT",
        "BODY",
        "CC",
        "BCC",
    }

    HEADER_CRITERIA ={
        "HEADER",
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

        def parse_one(
            start_index: int,
        ):
            if start_index >= len(criteria):
                raise IMAPSearchError(
                    "Missing SEARCH criterion"
                )

            criterion = (
                criteria[start_index].upper()
            )

            if criterion == "OR":
                left_predicate, next_index = (
                    parse_one(
                        start_index + 1
                    )
                )

                right_predicate, next_index = (
                    parse_one(
                        next_index
                    )
                )

                return (
                    lambda entry,
                    left=left_predicate,
                    right=right_predicate:
                    left(entry) or right(entry),
                    next_index,
                )

            if criterion == "NOT":
                nested_predicate, next_index = (
                    parse_one(
                        start_index + 1
                    )
                )

                return (
                    lambda entry,
                    predicate=nested_predicate:
                    not predicate(entry),
                    next_index,
                )

            if criterion in self.FLAG_CRITERIA:
                return (
                    self._build_flag_predicate(
                        criterion
                    ),
                    start_index + 1,
                )

            if criterion in self.VALUE_CRITERIA:
                if start_index + 1 >= len(criteria):
                    raise IMAPSearchError(
                        f"{criterion} requires a value"
                    )

                value = self._normalize_value(
                    criteria[start_index + 1]
                )

                return (
                    self._build_value_predicate(
                        criterion,
                        value,
                    ),
                    start_index + 2,
                )

            if criterion in self.HEADER_CRITERIA:
                if start_index + 2 >= len(criteria):
                    raise IMAPSearchError(
                        "HEADER requires field and value"
                    )

                field_name = self._normalize_value(
                    criteria[start_index + 1]
                )

                value = self._normalize_value(
                    criteria[start_index + 2]
                )

                return (
                    self._build_header_predicate(
                        field_name,
                        value,
                    ),
                    start_index + 3,
                )

            raise IMAPSearchError(
                "Unsupported SEARCH criterion "
                f"{criterion}"
            )

        while index < len(criteria):
            predicate, next_index = (
                parse_one(index)
            )

            predicates.append(predicate)
            index = next_index

        return predicates


    def _build_header_predicate(
        self,
        field_name: str,
        value: str,
    ):
        def predicate(
            entry: MessageEntry,
        ) -> bool:
            for name, header_value in (
                entry.message.headers.fields.items()
            ):
                if name.casefold() != field_name.casefold():
                    continue

                if isinstance(
                    header_value,
                    list,
                ):
                    return any(
                        self._contains(
                            str(item),
                            value,
                        )
                        for item in header_value
                    )

                return self._contains(
                    str(header_value),
                    value,
                )

            return False

        return predicate

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
            "DELETED": self._match_deleted,
            "UNDELETED": self._match_undeleted,
            "ANSWERED": self._match_answered,
            "UNANSWERED": self._match_unanswered,
            "DRAFT": self._match_draft,
            "UNDRAFT": self._match_undraft,
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

        if criterion == "CC":
            return lambda entry: self._contains(
                str(
                    entry.message.headers.fields.get(
                        "Cc",
                        "",
                    )
                ),
                value,
            )

        if criterion == "BCC":
            return lambda entry: self._contains(
                str(
                    entry.message.headers.fields.get(
                        "Bcc",
                        "",
                    )
                ),
                value,
            )

        if criterion == "BODY":
            return lambda entry: self._contains(
                entry.message.body or "",
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

    @staticmethod
    def _match_deleted(
        entry: MessageEntry,
    ) -> bool:
        return "\\Deleted" in entry.flags

    @staticmethod
    def _match_undeleted(
        entry: MessageEntry,
    ) -> bool:
        return "\\Deleted" not in entry.flags

    @staticmethod
    def _match_answered(
        entry: MessageEntry,
    ) -> bool:
        return "\\Answered" in entry.flags

    @staticmethod
    def _match_unanswered(
        entry: MessageEntry,
    ) -> bool:
        return "\\Answered" not in entry.flags

    @staticmethod
    def _match_draft(
        entry: MessageEntry,
    ) -> bool:
        return "\\Draft" in entry.flags

    @staticmethod
    def _match_undraft(
        entry: MessageEntry,
    ) -> bool:
        return "\\Draft" not in entry.flags