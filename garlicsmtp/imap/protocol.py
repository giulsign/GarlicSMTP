from garlicsmtp.imap.fetch import (
    IMAPFetchError,
    IMAPFetchRenderer,
)
from garlicsmtp.imap.parser import (
    IMAPParseError,
    IMAPParser,
)
from garlicsmtp.imap.reply import IMAPReply
from garlicsmtp.imap.response import IMAPResponse
from garlicsmtp.imap.session import (
    IMAPSession,
    IMAPSessionState,
)
from garlicsmtp.security.auth import (
    Authenticator,
    RejectingAuthenticator,
)
from garlicsmtp.storage.store import MessageStore
from garlicsmtp.imap.search import (
    IMAPSearchEngine,
    IMAPSearchError,
)
from garlicsmtp.storage.mailbox import (
    StoreOperation,
)
from garlicsmtp.imap.append import (
    IMAPAppendRequest,
)
from garlicsmtp.imap.message_parser import (
    IMAPMessageParseError,
    IMAPMessageParser,
)
from garlicsmtp.imap.command_result import (
    IMAPCommandResult,
)
from garlicsmtp.imap.command_result import (
    IMAPCommandAction,
    IMAPCommandResult,
)


class IMAPProtocol:

    def __init__(
        self,
        session: IMAPSession | None = None,
        authenticator: Authenticator | None = None,
        store: MessageStore | None = None,
    ):
        self.session = session or IMAPSession()

        self.authenticator = (
            authenticator
            or RejectingAuthenticator()
        )

        self.store = store or MessageStore()

    def _resolve_uid_sequence_set(
        self,
        uid_reference: str,
        existing_uids: set[int],
        *,
        require_explicit_uids: bool = True,
    ) -> list[int]:
        highest_uid = (
            max(existing_uids)
            if existing_uids
            else None
        )

        def resolve_uid(
            value: str,
        ) -> int:
            if value == "*":
                if highest_uid is None:
                    raise ValueError

                return highest_uid

            uid = int(value)

            if uid <= 0:
                raise ValueError

            return uid

        uids: list[int] = []

        for part in uid_reference.split(","):
            if ":" in part:
                start_text, end_text = part.split(
                    ":",
                    1,
                )

                start_uid = resolve_uid(
                    start_text
                )
                end_uid = resolve_uid(
                    end_text
                )

                lower = min(
                    start_uid,
                    end_uid,
                )
                upper = max(
                    start_uid,
                    end_uid,
                )

                uids.extend(
                    uid
                    for uid in range(
                        lower,
                        upper + 1,
                    )
                    if uid in existing_uids
                )

                continue

            uid = resolve_uid(part)

            if uid not in existing_uids:
                if require_explicit_uids:
                    raise LookupError

                continue

            uids.append(uid)

        return uids

    def _resolve_sequence_set(
        self,
        sequence_reference: str,
        message_count: int,
    ) -> list[int]:
        if message_count <= 0:
            return []

        def resolve_value(
            value: str,
        ) -> int:
            if value == "*":
                return message_count

            sequence_number = int(value)

            if sequence_number <= 0:
                raise ValueError

            return sequence_number

        sequence_numbers: list[int] = []

        for part in sequence_reference.split(","):
            if ":" in part:
                start_text, end_text = part.split(
                    ":",
                    1,
                )

                start = resolve_value(
                    start_text
                )

                end = resolve_value(
                    end_text
                )

                lower = min(
                    start,
                    end,
                )

                upper = max(
                    start,
                    end,
                )

                sequence_numbers.extend(
                    sequence_number
                    for sequence_number in range(
                        lower,
                        upper + 1,
                    )
                    if sequence_number <= message_count
                )

                continue

            sequence_number = resolve_value(
                part
            )

            if sequence_number <= message_count:
                sequence_numbers.append(
                    sequence_number
                )

        return sequence_numbers


    def greeting(
        self,
    ) -> list[IMAPResponse]:
        return [
            IMAPReply.untagged(
                "OK",
                "GarlicSMTP IMAP ready",
            )
        ]


    def _command_handler(
        self,
        command,
    ):
        return getattr(
            self,
            f"command_{command.name.lower()}",
            None,
        )
    

    def _execute_command(
        self,
        result: IMAPCommandResult,
    ) -> IMAPCommandResult:
        return result


    def _unsupported_command_reply(
        self,
        command,
    ) -> list[IMAPResponse]:
        return [
            IMAPReply.tagged(
                command.tag,
                "BAD",
                (
                    "Unsupported command "
                    f"{command.name}"
                ),
            )
        ]

    def execute(
        self,
        line: str,
    ) -> list[IMAPResponse]:

        try:
            command = IMAPParser.parse(
                line
            )

        except IMAPParseError as exc:

            return [
                IMAPReply.untagged(
                    "BAD",
                    str(exc),
                )
            ]

        handler = self._command_handler(
            command
        )

        if handler is None:
            return self._unsupported_command_reply(
                command
            )

        result = handler(command)

        if not isinstance(
            result,
            IMAPCommandResult,
        ):
            result = IMAPCommandResult.complete(
                result,
            )

        result = self._execute_command(
            result,
        )

        self._handle_command_action(
            result,
        )

        return result.as_list()
    
    def _handle_command_action(
        self,
        result: IMAPCommandResult,
    ) -> None:
        self._command_action = result.action

    def command_action(
        self,
    ) -> IMAPCommandAction:
        return self._command_action


    def command_idle(
        self,
        command,
    ) -> IMAPCommandResult:
        authentication_error = (
            self._require_authenticated(
                command,
            )
        )

        if authentication_error is not None:
            return IMAPCommandResult.complete(
                authentication_error,
            )

        if command.arguments:
            return IMAPCommandResult.complete(
                [
                    IMAPReply(
                        command.tag,
                        "BAD",
                        "IDLE does not accept arguments",
                    )
                ]
            )

        return IMAPCommandResult.enter_idle(
            []
        )


    def append_literal(
        self,
        request: IMAPAppendRequest,
        literal: bytes,
    ) -> list[IMAPReply]:
        return self.append_literals(
            request,
            [literal],
        )

    def append_literals(
        self,
        request: IMAPAppendRequest,
        literals: list[bytes] | tuple[bytes, ...],
    ) -> list[IMAPReply]:
        error_replies = self._validate_append_request(
            request,
            literals,
        )

        if error_replies is not None:
            return error_replies

        messages, error_replies = (
            self._parse_append_messages(
                request,
                literals,
            )
        )

        if error_replies is not None:
            return error_replies

        appended_uids = self._append_messages(
            request,
            messages,
        )

        return self._append_success_reply(
            request,
            appended_uids,
        )

    def _validate_append_request(
        self,
        request: IMAPAppendRequest,
        literals: list[bytes] | tuple[bytes, ...],
    ) -> list[IMAPReply] | None:
        if self.session.state is (
            IMAPSessionState.NOT_AUTHENTICATED
        ):
            return [
                IMAPReply.tagged(
                    request.tag,
                    "NO",
                    "Authentication required",
                )
            ]

        if request.mailbox not in (
            self.store.list_mailboxes()
        ):
            return [
                IMAPReply.tagged(
                    request.tag,
                    "NO",
                    "[TRYCREATE] Mailbox not found",
                )
            ]

        if len(literals) != len(request.items):
            return [
                IMAPReply.tagged(
                    request.tag,
                    "BAD",
                    (
                        "APPEND literal count "
                        "does not match"
                    ),
                )
            ]

        return None


    def _parse_append_messages(
        self,
        request: IMAPAppendRequest,
        literals: list[bytes] | tuple[bytes, ...],
    ) -> tuple[
        list,
        list[IMAPReply] | None,
    ]:
        messages = []   

        for item, literal in zip(
            request.items,
            literals,
            strict=True,
        ):
            if len(literal) != item.literal_size:
                return (
                    [],
                    [
                        IMAPReply.tagged(
                            request.tag,
                            "BAD",
                            (
                                "APPEND literal size "
                                "does not match"
                            ),
                        )
                    ],
                )

            try:
                message = IMAPMessageParser.parse(
                    literal
                )

            except IMAPMessageParseError as exc:
                return (
                    [],
                    [
                        IMAPReply.tagged(
                            request.tag,
                            "NO",
                            str(exc),
                        )
                    ],
                )

            messages.append(
                message
            )

        return messages, None
    

    def _append_messages(
        self,
        request: IMAPAppendRequest,
        messages,
    ) -> list[int]:
        mailbox = self.store.open_mailbox(
            request.mailbox
        )

        appended_uids = []

        for item, message in zip(
            request.items,
            messages,
            strict=True,
        ):
            appended = mailbox.append_message(
                message,
                flags=set(item.flags),
                internal_date=item.internal_date,
            )

            appended_uids.append(
                appended.uid
            )

        return appended_uids
    

    def _append_success_reply(
        self,
        request: IMAPAppendRequest,
        appended_uids: list[int],
    ) -> list[IMAPReply]:
        uid_set = ",".join(
            str(uid)
            for uid in appended_uids
        )

        return [
            IMAPReply.tagged(
                request.tag,
                "OK",
                (
                    f"[APPENDUID 1 {uid_set}] "
                    "APPEND completed"
                ),
            )
        ]


    def command_capability(
        self,
        command,
    ):
        if command.arguments:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "BAD",
                    "CAPABILITY does not accept arguments",
                )
            ]

        return [
            IMAPReply(
                (
                    "* CAPABILITY "
                    "IMAP4rev1 "
                    "UIDPLUS "
                    "UNSELECT "
                    "MOVE "
                    "NAMESPACE "
                    "ID "
                    "ENABLE "
                    "IDLE"
                )
            ),
            IMAPReply.tagged(
                command.tag,
                "OK",
                "CAPABILITY completed",
            ),
        ]
    

    def command_noop(
        self,
        command,
    ):
        return [
            IMAPReply.tagged(
                command.tag,
                "OK",
                "NOOP completed",
            )
        ]
    
    def command_check(
        self,
        command,
    ) -> list[IMAPResponse]:
        if self.session.state is not (
            IMAPSessionState.SELECTED
        ):
            return [
                IMAPReply.tagged(
                    command.tag,
                    "NO",
                    "Mailbox not selected",
                )
            ]

        if command.arguments:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "BAD",
                    "CHECK does not accept arguments",
                )
            ]

        if self.session.selected_mailbox is None:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "NO",
                    "Mailbox not selected",
                )
            ]

        return [
            IMAPReply.tagged(
                command.tag,
                "OK",
                "CHECK completed",
            )
        ]
    
    def command_logout(
        self,
        command,
    ):
        self.session.logout()

        return [
            IMAPReply.untagged(
                "BYE",
                "Logging out",
            ),
            IMAPReply.tagged(
                command.tag,
                "OK",
                "LOGOUT completed",
            ),
        ]
    

    def command_login(
        self,
        command,
    ):
        if (
            self.session.state
            is not IMAPSessionState.NOT_AUTHENTICATED
        ):
            return [
                IMAPReply.tagged(
                    command.tag,
                    "BAD",
                    "Already authenticated",
                )
            ]

        if len(command.arguments) != 2:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "BAD",
                    "LOGIN requires username and password",
                )
            ]

        username, password = command.arguments

        if not self.authenticator.authenticate(
            username,
            password,
        ):
            return [
                IMAPReply.tagged(
                    command.tag,
                    "NO",
                    "Authentication failed",
                )
            ]

        self.session.authenticate(
            username
        )

        return [
            IMAPReply.tagged(
                command.tag,
                "OK",
                "LOGIN completed",
            )
        ]
    
    def _list_mailboxes(
        self,
        tag,
        mailboxes,
        pattern,
        reply_name,
        completion_message,
    ):
        replies = []

        for mailbox in mailboxes:
            if not self._matches_mailbox_pattern(
                mailbox,
                pattern,
            ):
                continue

            replies.append(
                IMAPReply(
                    (
                        f'* {reply_name} () "/" '
                        f'"{mailbox}"'
                    )
                )
            )

        replies.append(
            IMAPReply.tagged(
                tag,
                "OK",
                completion_message,
            )
        )

        return replies

    def command_list(
        self,
        command,
    ):
        authentication_error = (
            self._require_authenticated(
                command
            )
        )

        if authentication_error is not None:
            return authentication_error

        if len(command.arguments) != 2:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "BAD",
                    "LIST requires reference and pattern",
                )
            ]

        reference, pattern = command.arguments

        if reference not in {"", '""'}:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "BAD",
                    "Unsupported LIST reference",
                )
            ]

        return self._list_mailboxes(
            command.tag,
            self.store.list_mailboxes(),
            pattern,
            "LIST",
            "LIST completed",
        )
    
    def command_lsub(
        self,
        command,
    ):
        authentication_error = (
            self._require_authenticated(
                command
            )
        )

        if authentication_error is not None:
            return authentication_error

        if len(command.arguments) != 2:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "BAD",
                    "LSUB requires reference and mailbox",
                )
            ]

        reference, pattern = command.arguments

        if reference not in {"", '""'}:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "BAD",
                    "Unsupported LSUB reference",
                )
            ]

        return self._list_mailboxes(
            command.tag,
            self.store.list_subscribed_mailboxes(),
            pattern,
            "LSUB",
            "LSUB completed",
        )

    def command_create(
        self,
        command,
    ):
        authentication_error = (
            self._require_authenticated(
                command
            )
        )

        if authentication_error is not None:
            return authentication_error

        if len(command.arguments) != 1:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "BAD",
                    "CREATE requires mailbox",
                )
            ]

        mailbox = command.arguments[0]

        if not self.store.create_mailbox(
            mailbox
        ):
            return [
                IMAPReply.tagged(
                    command.tag,
                    "NO",
                    "Mailbox already exists",
                )
            ]

        return [
            IMAPReply.tagged(
                command.tag,
                "OK",
                "CREATE completed",
            )
        ]
    
    def command_delete(
        self,
        command,
    ):
        authentication_error = (
            self._require_authenticated(
                command
            )
        )

        if authentication_error is not None:
            return authentication_error

        if len(command.arguments) != 1:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "BAD",
                    "DELETE requires mailbox",
                )
            ]

        mailbox = command.arguments[0]

        if not self.store.delete_mailbox(
            mailbox
        ):
            return [
                IMAPReply.tagged(
                    command.tag,
                    "NO",
                    "Mailbox not found",
                )
            ]

        return [
            IMAPReply.tagged(
                command.tag,
                "OK",
                "DELETE completed",
            )
        ]

    def command_rename(
        self,
        command,
    ):
        authentication_error = (
            self._require_authenticated(
                command
            )
        )

        if authentication_error is not None:
            return authentication_error

        if len(command.arguments) != 2:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "BAD",
                    "RENAME requires source and destination",
                )
            ]

        source = command.arguments[0]
        destination = command.arguments[1]

        if not self.store.rename_mailbox(
            source,
            destination,
        ):
            return [
                IMAPReply.tagged(
                    command.tag,
                    "NO",
                    "Unable to rename mailbox",
                )
            ]

        return [
            IMAPReply.tagged(
                command.tag,
                "OK",
                "RENAME completed",
            )
        ]

    def command_subscribe(
        self,
        command,
    ):
        authentication_error = (
            self._require_authenticated(
                command
            )
        )

        if authentication_error is not None:
            return authentication_error

        if len(command.arguments) != 1:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "BAD",
                    "SUBSCRIBE requires mailbox",
                )
            ]

        mailbox = command.arguments[0]

        if not self.store.subscribe_mailbox(
            mailbox
        ):
            return [
                IMAPReply.tagged(
                    command.tag,
                    "NO",
                    "Mailbox not found",
                )
            ]

        return [
            IMAPReply.tagged(
                command.tag,
                "OK",
                "SUBSCRIBE completed",
            )
        ]

    def command_unsubscribe(
        self,
        command,
    ):
        authentication_error = (
            self._require_authenticated(
                command
            )
        )

        if authentication_error is not None:
            return authentication_error

        if len(command.arguments) != 1:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "BAD",
                    "UNSUBSCRIBE requires mailbox",
                )
            ]

        mailbox = command.arguments[0]

        if not self.store.unsubscribe_mailbox(
            mailbox
        ):
            return [
                IMAPReply.tagged(
                    command.tag,
                    "NO",
                    "Mailbox not subscribed",
                )
            ]

        return [
            IMAPReply.tagged(
                command.tag,
                "OK",
                "UNSUBSCRIBE completed",
            )
        ]

    @staticmethod
    def _matches_mailbox_pattern(
        mailbox: str,
        pattern: str,
    ) -> bool:
        normalized = pattern.strip('"')

        if normalized == "*":
            return True

        if normalized == "%":
            return "/" not in mailbox

        return mailbox == normalized
    
    def _status_values(
        self,
        mailbox_view,
    ) -> dict[str, int]:
        return {
            "MESSAGES": mailbox_view.count(),
            "UIDNEXT": mailbox_view.next_uid(),
            "UIDVALIDITY": (
                mailbox_view.uid_validity()
            ),
            "UNSEEN": (
                mailbox_view.unseen_count()
            ),
            "HIGHESTMODSEQ": (
                mailbox_view.highest_modseq()
            ),
        }

    def _require_authenticated(
        self,
        command,
    ) -> list[IMAPResponse] | None:
        if self.session.state is (
            IMAPSessionState.NOT_AUTHENTICATED
        ):
            return [
                IMAPReply.tagged(
                    command.tag,
                    "NO",
                    "Authentication required",
                )
            ]

        return None

    def command_status(
        self,
        command,
    ) -> list[IMAPResponse]:
        authentication_error = (
            self._require_authenticated(
                command
            )
        )

        if authentication_error is not None:
            return authentication_error

        if len(command.arguments) < 2:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "BAD",
                    (
                        "STATUS requires mailbox "
                        "and data items"
                    ),
                )
            ]

        mailbox = command.arguments[0].strip(
            '"'
        )

        requested_items = (
            self._parse_status_items(
                command.arguments[1:]
            )
        )

        if not requested_items:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "BAD",
                    (
                        "STATUS requires at least "
                        "one data item"
                    ),
                )
            ]

        supported_items = {
            "MESSAGES",
            "UIDNEXT",
            "UIDVALIDITY",
            "UNSEEN",
            "HIGHESTMODSEQ",
        }

        for item in requested_items:
            if item not in supported_items:
                return [
                    IMAPReply.tagged(
                        command.tag,
                        "BAD",
                        (
                            "Unsupported STATUS item "
                            f"{item}"
                        ),
                    )
                ]

        if mailbox not in self.store.list_mailboxes():
            return [
                IMAPReply.tagged(
                    command.tag,
                    "NO",
                    "Mailbox not found",
                )
            ]

        mailbox_view = self.store.open_mailbox(
            mailbox
        )

        values = self._status_values(
            mailbox_view
        )

        status_values = " ".join(
            (
                f"{item} "
                f"{values[item]}"
            )
            for item in requested_items
        )

        return [
            IMAPReply(
                (
                    f'* STATUS "{mailbox}" '
                    f"({status_values})"
                )
            ),
            IMAPReply.tagged(
                command.tag,
                "OK",
                "STATUS completed",
            ),
        ]

    def command_select(
        self,
        command,
    ):
        authentication_error = (
            self._require_authenticated(
                command
            )
        )

        if authentication_error is not None:
            return authentication_error

        if len(command.arguments) != 1:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "BAD",
                    "SELECT requires mailbox",
                )
            ]

        mailbox = command.arguments[0].strip('"')

        if mailbox not in self.store.list_mailboxes():
            return [
                IMAPReply.tagged(
                    command.tag,
                    "NO",
                    "Mailbox not found",
                )
            ]

        mailbox_view = self.store.open_mailbox(
            mailbox
        )

        self.session.select(
            mailbox
        )

        replies = self._selection_replies(
            mailbox_view
        )

        replies.append(
            IMAPReply.tagged(
                command.tag,
                "OK",
                "[READ-WRITE] SELECT completed",
            )
        )

        return replies

    def _selection_replies(
        self,
        mailbox_view,
    ) -> list[IMAPResponse]:
        exists = mailbox_view.count()
        next_uid = mailbox_view.next_uid()
        uid_validity = (
            mailbox_view.uid_validity()
        )
        unseen_uid = (
            mailbox_view.first_unseen_uid()
        )

        replies: list[IMAPResponse] = [
            IMAPReply(
                "* FLAGS "
                "(\\Seen \\Answered \\Flagged "
                "\\Deleted \\Draft)"
            ),
            IMAPReply(
                "* OK [PERMANENTFLAGS "
                "(\\Seen \\Answered \\Flagged "
                "\\Deleted \\Draft)] "
                "Permanent flags"
            ),
            IMAPReply(
                f"* {exists} EXISTS"
            ),
            IMAPReply(
                "* 0 RECENT"
            ),
            IMAPReply(
                f"* OK [UIDVALIDITY {uid_validity}] "
                "UID validity"
            ),
            IMAPReply(
                f"* OK [UIDNEXT {next_uid}] "
                "Predicted next UID"
            ),
        ]

        if unseen_uid is not None:
            replies.append(
                IMAPReply(
                    f"* OK [UNSEEN {unseen_uid}] "
                    "First unseen message"
                )
            )

        return replies

    def command_examine(
        self,
        command,
    ):
        authentication_error = (
            self._require_authenticated(
                command
            )
        )

        if authentication_error is not None:
            return authentication_error

        if len(command.arguments) != 1:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "BAD",
                    "EXAMINE requires mailbox",
                )
            ]

        mailbox = command.arguments[0].strip('"')

        if mailbox not in self.store.list_mailboxes():
            return [
                IMAPReply.tagged(
                    command.tag,
                    "NO",
                    "Mailbox not found",
                )
            ]

        mailbox_view = self.store.open_mailbox(
            mailbox
        )

        self.session.select(
            mailbox,
            read_only=True,
        )

        replies = self._selection_replies(
            mailbox_view
        )

        replies.append(
            IMAPReply.tagged(
                command.tag,
                "OK",
                "[READ-ONLY] EXAMINE completed",
            )
        )

        return replies

    def command_uid(
        self,
        command,
    ) -> list[IMAPResponse]:
        if self.session.state is not (
            IMAPSessionState.SELECTED
        ):
            return [
                IMAPReply.tagged(
                    command.tag,
                    "NO",
                    "Mailbox not selected",
                )
            ]

        if not command.arguments:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "BAD",
                    "UID requires a subcommand",
                )
            ]

        subcommand = (
            command.arguments[0].upper()
        )

        if subcommand == "FETCH":
            return self._command_uid_fetch(
                command
            )

        if subcommand == "STORE":
            return self._command_uid_store(
                command
            )

        if subcommand == "SEARCH":
            return self._command_uid_search(
                command
            )

        if subcommand == "COPY":
            return self._command_uid_copy(
                command
            )

        if subcommand == "MOVE":
            return self._command_uid_move(
                command
            )

        return [
            IMAPReply.tagged(
                command.tag,
                "BAD",
                (
                    "Unsupported UID command "
                    f"{subcommand}"
                ),
            )
        ]


    def command_fetch(
        self,
        command,
    ) -> list[IMAPResponse]:
        if self.session.state is not (
            IMAPSessionState.SELECTED
        ):
            return [
                IMAPReply.tagged(
                    command.tag,
                    "NO",
                    "Mailbox not selected",
                )
            ]

        if len(command.arguments) < 2:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "BAD",
                    (
                        "FETCH requires sequence "
                        "number and data items"
                    ),
                )
            ]

        sequence_reference = (
            command.arguments[0]
        )

        requested_items = self._parse_fetch_items(
            command.arguments[1:]
        )

        mailbox = self.session.selected_mailbox

        if mailbox is None:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "NO",
                    "Mailbox not selected",
                )
            ]

        mailbox_view = self.store.open_mailbox(
            mailbox
        )

        try:
            sequence_numbers = (
                self._resolve_sequence_set(
                    sequence_reference,
                    mailbox_view.count(),
                )
            )
        except ValueError:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "BAD",
                    "Invalid sequence number",
                )
            ]

        replies: list[IMAPResponse] = []

        for sequence_number in sequence_numbers:
            selected = (
                mailbox_view.get_by_sequence_number(
                    sequence_number
                )
            )

            if selected is None:
                continue

            renderer = IMAPFetchRenderer(
                entry=selected,
                sequence_number=sequence_number,
            )

            try:
                response = renderer.render(
                    requested_items
                )
            except IMAPFetchError as exc:
                return [
                    IMAPReply.tagged(
                        command.tag,
                        "BAD",
                        str(exc),
                    )
                ]

            if (
                renderer.mark_seen
                and "\\Seen" not in selected.flags
            ):
                updated = mailbox_view.add_flags(
                    selected.id,
                    {
                        "\\Seen",
                    },
                )

                if updated:
                    refreshed = mailbox_view.get_by_id(
                        selected.id
                    )

                    if refreshed is not None:
                        renderer = IMAPFetchRenderer(
                            entry=refreshed,
                            sequence_number=(
                                sequence_number
                            ),
                        )

                        response = renderer.render(
                            requested_items
                        )

            replies.append(response)

        replies.append(
            IMAPReply.tagged(
                command.tag,
                "OK",
                "FETCH completed",
            )
        )

        return replies


    def command_store(
        self,
        command,
    ) -> list[IMAPResponse]:
        if self.session.state is not (
            IMAPSessionState.SELECTED
        ):
            return [
                IMAPReply.tagged(
                    command.tag,
                    "NO",
                    "Mailbox not selected",
                )
            ]

        if len(command.arguments) < 3:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "BAD",
                    (
                        "STORE requires sequence "
                        "number, operation and flags"
                    ),
                )
            ]

        sequence_reference = (
            command.arguments[0]
        )

        operation_text = (
            command.arguments[1].upper()
        )

        operation_map = {
            "FLAGS": StoreOperation.SET,
            "FLAGS.SILENT": StoreOperation.SET,
            "+FLAGS": StoreOperation.ADD,
            "+FLAGS.SILENT": StoreOperation.ADD,
            "-FLAGS": StoreOperation.REMOVE,
            "-FLAGS.SILENT": StoreOperation.REMOVE,
        }

        operation = operation_map.get(
            operation_text
        )

        if operation is None:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "BAD",
                    (
                        "Unsupported STORE operation "
                        f"{operation_text}"
                    ),
                )
            ]

        if self.session.selected_mailbox_read_only:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "NO",
                    "Mailbox is read-only",
                )
            ]

        mailbox = self.session.selected_mailbox

        if mailbox is None:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "NO",
                    "Mailbox not selected",
                )
            ]

        silent = operation_text.endswith(
            ".SILENT"
        )

        flags = self._parse_store_flags(
            command.arguments[2:]
        )

        mailbox_view = self.store.open_mailbox(
            mailbox
        )

        try:
            sequence_numbers = (
                self._resolve_sequence_set(
                    sequence_reference,
                    mailbox_view.count(),
                )
            )
        except ValueError:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "BAD",
                    "Invalid sequence number",
                )
            ]

        uids: list[int] = []

        for sequence_number in sequence_numbers:
            entry = (
                mailbox_view.get_by_sequence_number(
                    sequence_number
                )
            )

            if entry is None:
                continue

            uids.append(entry.uid)

        return self._store_flags_for_uids(
            command=command,
            mailbox_view=mailbox_view,
            uids=uids,
            operation=operation,
            flags=flags,
            silent=silent,
            include_uid=False,
            completion_text="STORE completed",
        )
    

    def _command_uid_fetch(
        self,
        command,
    ) -> list[IMAPResponse]:
        if len(command.arguments) < 3:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "BAD",
                    (
                        "UID FETCH requires UID "
                        "and data items"
                    ),
                )
            ]

        uid_reference = command.arguments[1]

        requested_items = self._parse_fetch_items(
            command.arguments[2:]
        )

        mailbox = self.session.selected_mailbox

        if mailbox is None:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "NO",
                    "Mailbox not selected",
                )
            ]

        mailbox_view = self.store.open_mailbox(
            mailbox
        )

        entries = self.store.list_entries(
            mailbox
        )

        existing_uids = {
            entry.uid
            for entry in entries
        }

        try:
            uids = self._resolve_uid_sequence_set(
                uid_reference,
                existing_uids,
                require_explicit_uids=False,
            )
        except ValueError:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "BAD",
                    "Invalid UID",
                )
            ]

        replies: list[IMAPResponse] = []

        for uid in uids:
            result = mailbox_view.fetch_by_uid(
                uid
            )

            if result is None:
                continue

            sequence_number, selected = result

            renderer = IMAPFetchRenderer(
                entry=selected,
                sequence_number=sequence_number,
            )

            try:
                response = renderer.render(
                    requested_items
                )
            except IMAPFetchError as exc:
                return [
                    IMAPReply.tagged(
                        command.tag,
                        "BAD",
                        str(exc),
                    )
                ]

            if (
                renderer.mark_seen
                and "\\Seen" not in selected.flags
            ):
                updated = mailbox_view.add_flags(
                    selected.id,
                    {
                        "\\Seen",
                    },
                )

                if updated:
                    refreshed = mailbox_view.get_by_id(
                        selected.id
                    )

                    if refreshed is not None:
                        renderer = IMAPFetchRenderer(
                            entry=refreshed,
                            sequence_number=(
                                sequence_number
                            ),
                        )

                        response = renderer.render(
                            requested_items
                        )

            replies.append(response)

        replies.append(
            IMAPReply.tagged(
                command.tag,
                "OK",
                "UID FETCH completed",
            )
        )

        return replies
    
  
    @staticmethod
    def _parse_fetch_items(
        arguments: list[str],
    ) -> set[str]:
        text = " ".join(arguments).strip()

        if (
            text.startswith("(")
            and text.endswith(")")
        ):
            text = text[1:-1]

        items: list[str] = []
        current: list[str] = []
        bracket_depth = 0

        for character in text:
            if character == "[":
                bracket_depth += 1

            elif character == "]":
                bracket_depth -= 1

            if (
                character.isspace()
                and bracket_depth == 0
            ):
                if current:
                    items.append(
                        "".join(current)
                    )
                    current = []

                continue

            current.append(character)

        if current:
            items.append(
                "".join(current)
            )

        parsed_items = {
            item.upper()
            for item in items
            if item
        }

        if "FAST" in parsed_items:
            parsed_items.remove(
                "FAST"
            )

            parsed_items.update(
                {
                    "FLAGS",
                    "INTERNALDATE",
                    "RFC822.SIZE",
                }
            )

        if "ALL" in parsed_items:
            parsed_items.remove(
                "ALL"
            )

            parsed_items.update(
                {
                    "FLAGS",
                    "INTERNALDATE",
                    "RFC822.SIZE",
                    "ENVELOPE",
                }
            )

        if "FULL" in parsed_items:
            parsed_items.remove(
                "FULL"
            )

            parsed_items.update(
                {
                    "FLAGS",
                    "INTERNALDATE",
                    "RFC822.SIZE",
                    "ENVELOPE",
                    "BODY",
                }
            )

        return parsed_items
    
    @staticmethod
    def _parse_status_items(
        arguments: list[str],
    ) -> list[str]:
        text = " ".join(arguments).strip()

        if (
            text.startswith("(")
            and text.endswith(")")
        ):
            text = text[1:-1]

        return [
            item.upper()
            for item in text.split()
            if item
        ]
    

    def _command_uid_store(
        self,
        command,
    ) -> list[IMAPResponse]:
        if len(command.arguments) < 4:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "BAD",
                    (
                        "UID STORE requires UID, "
                        "operation and flags"
                    ),
                )
            ]

        uid_reference = command.arguments[1]

        operation_text = (
            command.arguments[2].upper()
        )

        operation_map = {
            "FLAGS": StoreOperation.SET,
            "FLAGS.SILENT": StoreOperation.SET,
            "+FLAGS": StoreOperation.ADD,
            "+FLAGS.SILENT": StoreOperation.ADD,
            "-FLAGS": StoreOperation.REMOVE,
            "-FLAGS.SILENT": StoreOperation.REMOVE,
        }

        operation = operation_map.get(
            operation_text
        )

        if operation is None:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "BAD",
                    (
                        "Unsupported STORE operation "
                        f"{operation_text}"
                    ),
                )
            ]

        silent = operation_text.endswith(
            ".SILENT"
        )

        flags = self._parse_store_flags(
            command.arguments[3:]
        )

        mailbox = self.session.selected_mailbox

        if self.session.selected_mailbox_read_only:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "NO",
                    "Mailbox is read-only",
                )
            ]

        if mailbox is None:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "NO",
                    "Mailbox not selected",
                )
            ]

        mailbox_view = self.store.open_mailbox(
            mailbox
        )

        entries = self.store.list_entries(
            mailbox
        )

        existing_uids = {
            entry.uid
            for entry in entries
        }

        try:
            uids = self._resolve_uid_sequence_set(
                uid_reference,
                existing_uids,
                require_explicit_uids=False,
            )
        except ValueError:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "BAD",
                    "Invalid UID",
                )
            ]

        return self._store_flags_for_uids(
            command=command,
            mailbox_view=mailbox_view,
            uids=uids,
            operation=operation,
            flags=flags,
            silent=silent,
            include_uid=True,
            completion_text=(
                "UID STORE completed"
            ),
        )

    def _store_flags_for_uids(
        self,
        *,
        command,
        mailbox_view,
        uids: list[int],
        operation: StoreOperation,
        flags: set[str],
        silent: bool,
        include_uid: bool,
        completion_text: str,
    ) -> list[IMAPResponse]:
        replies: list[IMAPResponse] = []

        for uid in uids:
            result = mailbox_view.store_flags(
                uid=uid,
                operation=operation,
                flags=flags,
            )

            if result is None:
                continue

            sequence_number, refreshed = result

            if silent:
                continue

            requested_items = {
                "FLAGS",
            }

            if include_uid:
                requested_items.add(
                    "UID"
                )

            renderer = IMAPFetchRenderer(
                entry=refreshed,
                sequence_number=sequence_number,
            )

            replies.append(
                renderer.render(
                    requested_items
                )
            )

        replies.append(
            IMAPReply.tagged(
                command.tag,
                "OK",
                completion_text,
            )
        )

        return replies

    def command_copy(
        self,
        command,
    ) -> list[IMAPResponse]:
        if self.session.state is not (
            IMAPSessionState.SELECTED
        ):
            return [
                IMAPReply.tagged(
                    command.tag,
                    "NO",
                    "Mailbox not selected",
                )
            ]

        if len(command.arguments) != 2:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "BAD",
                    (
                        "COPY requires sequence "
                        "set and destination mailbox"
                    ),
                )
            ]

        sequence_reference = (
            command.arguments[0]
        )

        destination_mailbox = (
            command.arguments[1].strip('"')
        )

        selected_mailbox = (
            self.session.selected_mailbox
        )

        if selected_mailbox is None:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "NO",
                    "Mailbox not selected",
                )
            ]

        if (
            destination_mailbox
            not in self.store.list_mailboxes()
        ):
            return [
                IMAPReply.tagged(
                    command.tag,
                    "NO",
                    "Destination mailbox not found",
                )
            ]

        mailbox_view = self.store.open_mailbox(
            selected_mailbox
        )

        try:
            sequence_numbers = (
                self._resolve_sequence_set(
                    sequence_reference,
                    mailbox_view.count(),
                )
            )
        except ValueError:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "BAD",
                    "Invalid sequence number",
                )
            ]

        source_uids: list[int] = []
        destination_uids: list[int] = []

        for sequence_number in sequence_numbers:
            entry = (
                mailbox_view.get_by_sequence_number(
                    sequence_number
                )
            )

            if entry is None:
                continue

            copied = mailbox_view.copy_by_uid(
                entry.uid,
                destination_mailbox,
            )

            if copied is None:
                continue

            source_uid, destination_uid = copied

            source_uids.append(source_uid)
            destination_uids.append(
                destination_uid
            )

        if not source_uids:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "OK",
                    "COPY completed",
                )
            ]

        source_set = ",".join(
            str(uid)
            for uid in source_uids
        )

        destination_set = ",".join(
            str(uid)
            for uid in destination_uids
        )

        return [
            IMAPReply.tagged(
                command.tag,
                "OK",
                (
                    "[COPYUID 1 "
                    f"{source_set} "
                    f"{destination_set}] "
                    "COPY completed"
                ),
            )
        ]
    
    def _command_uid_copy(
        self,
        command,
    ) -> list[IMAPResponse]:
        if len(command.arguments) != 3:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "BAD",
                    (
                        "UID COPY requires UID "
                        "and destination mailbox"
                    ),
                )
            ]

        uid_reference = command.arguments[1]

        destination_mailbox = (
            command.arguments[2].strip('"')
        )

        selected_mailbox = (
            self.session.selected_mailbox
        )

        if selected_mailbox is None:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "NO",
                    "Mailbox not selected",
                )
            ]

        if (
            destination_mailbox
            not in self.store.list_mailboxes()
        ):
            return [
                IMAPReply.tagged(
                    command.tag,
                    "NO",
                    "Destination mailbox not found",
                )
            ]

        mailbox_view = self.store.open_mailbox(
            selected_mailbox
        )

        entries = self.store.list_entries(
            selected_mailbox
        )

        existing_uids = {
            entry.uid
            for entry in entries
        }

        try:
            uids = self._resolve_uid_sequence_set(
                uid_reference,
                existing_uids,
            )
        except ValueError:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "BAD",
                    "Invalid UID",
                )
            ]
        except LookupError:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "NO",
                    "Message not found",
                )
            ]

        if not uids:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "NO",
                    "Message not found",
                )
            ]

        source_uids: list[int] = []
        destination_uids: list[int] = []

        for uid in uids:
            copied = mailbox_view.copy_by_uid(
                uid,
                destination_mailbox,
            )

            if copied is None:
                return [
                    IMAPReply.tagged(
                        command.tag,
                        "NO",
                        "Message not found",
                    )
                ]

            source_uid, destination_uid = copied

            source_uids.append(source_uid)
            destination_uids.append(
                destination_uid
            )

        source_set = ",".join(
            str(uid)
            for uid in source_uids
        )

        destination_set = ",".join(
            str(uid)
            for uid in destination_uids
        )

        return [
            IMAPReply.tagged(
                command.tag,
                "OK",
                (
                    "[COPYUID 1 "
                    f"{source_set} "
                    f"{destination_set}] "
                    "UID COPY completed"
                ),
            )
        ]
    

    def _command_uid_move(
        self,
        command,
    ) -> list[IMAPResponse]:
        if len(command.arguments) != 3:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "BAD",
                    (
                        "UID MOVE requires UID "
                        "and destination mailbox"
                    ),
                )
            ]

        uid_reference = command.arguments[1]

        destination_mailbox = (
            command.arguments[2].strip('"')
        )

        selected_mailbox = (
            self.session.selected_mailbox
        )

        if self.session.selected_mailbox_read_only:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "NO",
                    "Mailbox is read-only",
                )
            ]

        if selected_mailbox is None:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "NO",
                    "Mailbox not selected",
                )
            ]

        if (
            destination_mailbox
            == selected_mailbox
        ):
            return [
                IMAPReply.tagged(
                    command.tag,
                    "NO",
                    (
                        "Destination mailbox must "
                        "differ from selected mailbox"
                    ),
                )
            ]

        if (
            destination_mailbox
            not in self.store.list_mailboxes()
        ):
            return [
                IMAPReply.tagged(
                    command.tag,
                    "NO",
                    "Destination mailbox not found",
                )
            ]

        mailbox_view = self.store.open_mailbox(
            selected_mailbox
        )

        entries = self.store.list_entries(
            selected_mailbox
        )

        existing_uids = {
            entry.uid
            for entry in entries
        }

        try:
            uids = self._resolve_uid_sequence_set(
                uid_reference,
                existing_uids,
            )
        except ValueError:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "BAD",
                    "Invalid UID",
                )
            ]
        except LookupError:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "NO",
                    "Message not found",
                )
            ]

        if not uids:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "NO",
                    "Message not found",
                )
            ]

        replies: list[IMAPResponse] = []
        source_uids: list[int] = []
        destination_uids: list[int] = []

        for uid in uids:
            moved = mailbox_view.move_by_uid(
                uid,
                destination_mailbox,
            )

            if moved is None:
                return [
                    IMAPReply.tagged(
                        command.tag,
                        "NO",
                        "Message not found",
                    )
                ]

            (
                source_uid,
                destination_uid,
                sequence_number,
            ) = moved

            replies.append(
                IMAPReply(
                    (
                        f"* {sequence_number} "
                        "EXPUNGE"
                    )
                )
            )

            source_uids.append(source_uid)
            destination_uids.append(
                destination_uid
            )

        source_set = ",".join(
            str(uid)
            for uid in source_uids
        )

        destination_set = ",".join(
            str(uid)
            for uid in destination_uids
        )

        replies.append(
            IMAPReply.tagged(
                command.tag,
                "OK",
                (
                    "[COPYUID 1 "
                    f"{source_set} "
                    f"{destination_set}] "
                    "UID MOVE completed"
                ),
            )
        )

        return replies

        def resolve_uid(
            value: str,
        ) -> int:
            if value == "*":
                if highest_uid is None:
                    raise ValueError

                return highest_uid

            uid = int(value)

            if uid <= 0:
                raise ValueError

            return uid

        try:
            uids: list[int] = []

            for part in uid_reference.split(","):
                if ":" in part:
                    start_text, end_text = part.split(
                        ":",
                        1,
                    )

                    start_uid = resolve_uid(
                        start_text
                    )
                    end_uid = resolve_uid(
                        end_text
                    )

                    lower = min(
                        start_uid,
                        end_uid,
                    )
                    upper = max(
                        start_uid,
                        end_uid,
                    )

                    uids.extend(
                        uid
                        for uid in range(
                            lower,
                            upper + 1,
                        )
                        if uid in existing_uids
                    )
                else:
                    uid = resolve_uid(part)

                    if uid not in existing_uids:
                        return [
                            IMAPReply.tagged(
                                command.tag,
                                "NO",
                                "Message not found",
                            )
                        ]

                    uids.append(uid)

        except ValueError:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "BAD",
                    "Invalid UID",
                )
            ]

        if not uids:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "BAD",
                    "Invalid UID",
                )
            ]

        replies: list[IMAPResponse] = []
        source_uids: list[int] = []
        destination_uids: list[int] = []

        for uid in uids:
            moved = mailbox_view.move_by_uid(
                uid,
                destination_mailbox,
            )

            if moved is None:
                return [
                    IMAPReply.tagged(
                        command.tag,
                        "NO",
                        "Message not found",
                    )
                ]

            (
                source_uid,
                destination_uid,
                sequence_number,
            ) = moved

            replies.append(
                IMAPReply(
                    (
                        f"* {sequence_number} "
                        "EXPUNGE"
                    )
                )
            )

            source_uids.append(source_uid)
            destination_uids.append(
                destination_uid
            )

        source_set = ",".join(
            str(uid)
            for uid in source_uids
        )

        destination_set = ",".join(
            str(uid)
            for uid in destination_uids
        )

        replies.append(
            IMAPReply.tagged(
                command.tag,
                "OK",
                (
                    "[COPYUID 1 "
                    f"{source_set} "
                    f"{destination_set}] "
                    "UID MOVE completed"
                ),
            )
        )

        return replies

    @staticmethod
    def _parse_store_flags(
        arguments: list[str],
    ) -> set[str]:
        text = " ".join(arguments).strip()

        if (
            text.startswith("(")
            and text.endswith(")")
        ):
            text = text[1:-1]

        return {
            flag
            for flag in text.split()
            if flag
        }
    

    def _command_uid_search(
        self,
        command,
    ) -> list[IMAPResponse]:
        if len(command.arguments) < 2:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "BAD",
                    "UID SEARCH requires criteria",
                )
            ]

        mailbox = self.session.selected_mailbox

        if mailbox is None:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "NO",
                    "Mailbox not selected",
                )
            ]

        criteria = command.arguments[1:]

        mailbox_view = self.store.open_mailbox(
            mailbox
        )

        engine = IMAPSearchEngine(
            entries=mailbox_view.list_entries()
        )

        try:
            matching_uids = engine.search(
                criteria
            )
        except IMAPSearchError as exc:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "BAD",
                    str(exc),
                )
            ]

        if matching_uids:
            search_reply = (
                "* SEARCH "
                + " ".join(
                    str(uid)
                    for uid in matching_uids
                )
            )
        else:
            search_reply = "* SEARCH"

        return [
            IMAPReply(search_reply),
            IMAPReply.tagged(
                command.tag,
                "OK",
                "UID SEARCH completed",
            ),
        ]

    def command_search(
        self,
        command,
    ) -> list[IMAPResponse]:
        if self.session.state is not (
            IMAPSessionState.SELECTED
        ):
            return [
                IMAPReply.tagged(
                    command.tag,
                    "NO",
                    "Mailbox not selected",
                )
            ]

        if not command.arguments:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "BAD",
                    "SEARCH requires criteria",
                )
            ]

        mailbox = self.session.selected_mailbox

        if mailbox is None:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "NO",
                    "Mailbox not selected",
                )
            ]

        criteria = command.arguments

        mailbox_view = self.store.open_mailbox(
            mailbox
        )

        engine = IMAPSearchEngine(
            entries=mailbox_view.list_entries()
        )

        try:
            matching_uids = engine.search(
                criteria
            )
        except IMAPSearchError as exc:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "BAD",
                    str(exc),
                )
            ]

        sequence_numbers: list[int] = []

        for uid in matching_uids:
            sequence_number = (
                mailbox_view.get_sequence_number(
                    uid
                )
            )

            if sequence_number is not None:
                sequence_numbers.append(
                    sequence_number
                )

        if sequence_numbers:
            search_reply = (
                "* SEARCH "
                + " ".join(
                    str(sequence_number)
                    for sequence_number
                    in sequence_numbers
                )
            )
        else:
            search_reply = "* SEARCH"

        return [
            IMAPReply(search_reply),
            IMAPReply.tagged(
                command.tag,
                "OK",
                "SEARCH completed",
            ),
        ]

    def command_expunge(
        self,
        command,
    ) -> list[IMAPResponse]:
        if self.session.state is not (
            IMAPSessionState.SELECTED
        ):
            return [
                IMAPReply.tagged(
                    command.tag,
                    "NO",
                    "Mailbox not selected",
                )
            ]

        if command.arguments:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "BAD",
                    "EXPUNGE does not accept arguments",
                )
            ]

        mailbox = self.session.selected_mailbox

        if self.session.selected_mailbox_read_only:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "NO",
                    "Mailbox is read-only",
                )
            ]
        
        if mailbox is None:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "NO",
                    "Mailbox not selected",
                )
            ]

        mailbox_view = self.store.open_mailbox(
            mailbox
        )

        sequence_numbers = (
            mailbox_view.expunge_deleted()
        )

        replies: list[IMAPResponse] = [
            IMAPReply(
                f"* {sequence_number} EXPUNGE"
            )
            for sequence_number
            in sequence_numbers
        ]

        replies.append(
            IMAPReply.tagged(
                command.tag,
                "OK",
                "EXPUNGE completed",
            )
        )

        return replies
    
    def command_close(
        self,
        command,
    ) -> list[IMAPResponse]:
        if self.session.state is not (
            IMAPSessionState.SELECTED
        ):
            return [
                IMAPReply.tagged(
                    command.tag,
                    "NO",
                    "Mailbox not selected",
                )
            ]

        if command.arguments:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "BAD",
                    "CLOSE does not accept arguments",
                )
            ]

        mailbox = self.session.selected_mailbox

        if self.session.selected_mailbox_read_only:
            self.session.close_mailbox()

            return [
                IMAPReply.tagged(
                    command.tag,
                    "OK",
                    "CLOSE completed",
                )
            ]

        if mailbox is None:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "NO",
                    "Mailbox not selected",
                )
            ]

        mailbox_view = self.store.open_mailbox(
            mailbox
        )

        mailbox_view.expunge_deleted()

        self.session.close_mailbox()

        return [
            IMAPReply.tagged(
                command.tag,
                "OK",
                "CLOSE completed",
            )
        ]
    
    def command_unselect(
        self,
        command,
    ) -> list[IMAPResponse]:
        if self.session.state is not (
            IMAPSessionState.SELECTED
        ):
            return [
                IMAPReply.tagged(
                    command.tag,
                    "NO",
                    "Mailbox not selected",
                )
            ]

        if command.arguments:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "BAD",
                    (
                        "UNSELECT does not "
                        "accept arguments"
                    ),
                )
            ]

        if self.session.selected_mailbox is None:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "NO",
                    "Mailbox not selected",
                )
            ]

        self.session.close_mailbox()

        return [
            IMAPReply.tagged(
                command.tag,
                "OK",
                "UNSELECT completed",
            )
        ]
    
    def command_namespace(
        self,
        command,
    ):
        authentication_error = (
            self._require_authenticated(
                command
            )
        )

        if authentication_error is not None:
            return authentication_error

        if command.arguments:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "BAD",
                    "NAMESPACE does not accept arguments",
                )
            ]

        return [
            IMAPReply(
                '* NAMESPACE (("" "/")) NIL NIL'
            ),
            IMAPReply.tagged(
                command.tag,
                "OK",
                "NAMESPACE completed",
            ),
        ]


    def command_id(
        self,
        command,
    ):
        authentication_error = (
            self._require_authenticated(
                command
            )
        )

        if authentication_error is not None:
            return authentication_error

        if len(command.arguments) > 1:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "BAD",
                    "ID accepts zero or one argument",
                )
            ]

        return [
            IMAPReply(
                (
                    '* ID ('
                    '"name" "GarlicSMTP" '
                    '"version" "1.0"'
                    ')'
                )
            ),
            IMAPReply.tagged(
                command.tag,
                "OK",
                "ID completed",
            ),
        ]
    

    def command_enable(
        self,
        command,
    ):
        authentication_error = (
            self._require_authenticated(
                command
            )
        )

        if authentication_error is not None:
            return authentication_error

        if not command.arguments:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "BAD",
                    "ENABLE requires one or more capabilities",
                )
            ]

        return [
            IMAPReply.tagged(
                command.tag,
                "OK",
                "ENABLE completed",
            )
        ]