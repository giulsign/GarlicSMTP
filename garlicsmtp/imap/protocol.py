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


    def greeting(
        self,
    ) -> list[IMAPResponse]:
        return [
            IMAPReply.untagged(
                "OK",
                "GarlicSMTP IMAP ready",
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

        handler = getattr(
            self,
            f"command_{command.name.lower()}",
            None,
        )

        if handler is None:

            return [
                IMAPReply.tagged(
                    command.tag,
                    "BAD",
                    f"Unsupported command {command.name}",
                )
            ]

        return handler(command)
    
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
    ) -> list[IMAPResponse]:
        return [
            IMAPReply.untagged(
                "CAPABILITY",
                (
                    "IMAP4rev1 "
                    "UIDPLUS "
                    "UNSELECT "
                    "MOVE"
                ),
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
    

    def command_list(
        self,
        command,
    ):
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

        mailboxes = self.store.list_mailboxes()

        replies = []

        for mailbox in mailboxes:
            if not self._matches_mailbox_pattern(
                mailbox,
                pattern,
            ):
                continue

            replies.append(
                IMAPReply(
                    f'* LIST () "/" "{mailbox}"'
                )
            )

        replies.append(
            IMAPReply.tagged(
                command.tag,
                "OK",
                "LIST completed",
            )
        )

        return replies
    

    def command_create(
        self,
        command,
    ):
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
    
    def command_status(
        self,
        command,
    ) -> list[IMAPResponse]:
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
            "UNSEEN",
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

        values = {
            "MESSAGES": mailbox_view.count(),
            "UIDNEXT": mailbox_view.next_uid(),
            "UNSEEN": (
                mailbox_view.unseen_count()
            ),
        }

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

        exists = mailbox_view.count()
        next_uid = mailbox_view.next_uid()
        unseen_uid = (
            mailbox_view.first_unseen_uid()
        )

        self.session.select(
            mailbox
        )

        replies = [
            IMAPReply(
                "* FLAGS "
                "(\\Seen \\Answered \\Flagged "
                "\\Deleted \\Draft)"
            ),
            IMAPReply(
                f"* {exists} EXISTS"
            ),
            IMAPReply(
                "* 0 RECENT"
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

        replies.append(
            IMAPReply.tagged(
                command.tag,
                "OK",
                "[READ-WRITE] SELECT completed",
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

        try:
            uid = int(uid_reference)
        except ValueError:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "BAD",
                    "Invalid UID",
                )
            ]

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

        result = mailbox_view.fetch_by_uid(
            uid
        )

        replies: list[IMAPResponse] = []

        if result is not None:
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

        return {
            item.upper()
            for item in text.split()
            if item
        }
    
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

        try:
            uid = int(uid_reference)
        except ValueError:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "BAD",
                    "Invalid UID",
                )
            ]

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

        result = mailbox_view.store_flags(
            uid=uid,
            operation=operation,
            flags=flags,
        )

        replies: list[IMAPResponse] = []

        if result is not None:
            sequence_number, refreshed = result

            if not silent:
                renderer = IMAPFetchRenderer(
                    entry=refreshed,
                    sequence_number=(
                        sequence_number
                    ),
                )

                replies.append(
                    renderer.render(
                        {
                            "FLAGS",
                            "UID",
                        }
                    )
                )

        replies.append(
            IMAPReply.tagged(
                command.tag,
                "OK",
                "UID STORE completed",
            )
        )

        return replies
    
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

        try:
            uid = int(uid_reference)
        except ValueError:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "BAD",
                    "Invalid UID",
                )
            ]

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

        return [
            IMAPReply.tagged(
                command.tag,
                "OK",
                (
                    "[COPYUID 1 "
                    f"{source_uid} "
                    f"{destination_uid}] "
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

        try:
            uid = int(uid_reference)
        except ValueError:
            return [
                IMAPReply.tagged(
                    command.tag,
                    "BAD",
                    "Invalid UID",
                )
            ]

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

        return [
            IMAPReply(
                (
                    f"* {sequence_number} "
                    "EXPUNGE"
                )
            ),
            IMAPReply.tagged(
                command.tag,
                "OK",
                (
                    "[COPYUID 1 "
                    f"{source_uid} "
                    f"{destination_uid}] "
                    "UID MOVE completed"
                ),
            ),
        ]

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