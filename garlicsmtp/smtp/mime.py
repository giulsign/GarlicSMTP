# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

from quopri import decodestring
from email import policy
from email.parser import Parser
import base64
from dataclasses import dataclass

@dataclass(frozen=True)
class MimeAttachment:
    filename: str
    declared_mime: str
    content: bytes

class MimeEncoder:

    @staticmethod
    def encode_multipart_mixed(
        *,
        text: str,
        attachments: list[MimeAttachment],
        boundary: str,
    ) -> str:
        lines = [
            f"--{boundary}",
            "Content-Type: text/plain; charset=utf-8",
            "",
            text,
        ]

        for attachment in attachments:
            encoded_content = base64.b64encode(
                attachment.content
            ).decode("ascii")

            lines.extend(
                [
                    f"--{boundary}",
                    (
                        "Content-Type: "
                        f"{attachment.declared_mime}"
                    ),
                    (
                        "Content-Disposition: attachment; "
                        f'filename="{attachment.filename}"'
                    ),
                    "Content-Transfer-Encoding: base64",
                    "",
                    encoded_content,
                ]
            )

        lines.append(
            f"--{boundary}--"
        )

        return "\r\n".join(lines)

class MimeDecoder:

    @staticmethod
    def decode(
        body: str,
        encoding: str,
    ) -> str:

        normalized = encoding.strip().lower()

        if normalized == "quoted-printable":
            return decodestring(
                body.encode("utf-8")
            ).decode(
                "utf-8"
            )
        
        if normalized == "base64":
            return base64.b64decode(
                body.encode("ascii"),
                validate=True,
            ).decode("utf-8")
        
        return body

    @staticmethod
    def extract_multipart_alternative(
        body: str,
        boundary: str,
    ) -> str:

        message = Parser(
            policy=policy.default
        ).parsestr(
            (
                "Content-Type: multipart/alternative; "
                f'boundary="{boundary}"\n'
                "\n"
                f"{body}"
            )
        )

        if not message.is_multipart():
            raise ValueError(
                "Invalid multipart body"
            )

        for part in message.iter_parts():
            if part.get_content_type() != "text/plain":
                continue

            content = part.get_content()

            if isinstance(
                content,
                str,
            ):
                return content.strip()

        raise ValueError(
            "Multipart body has no text/plain part"
        )

    @staticmethod
    def extract_multipart_mixed(
        body: str,
        boundary: str,
    ) -> tuple[
        str,
        list[MimeAttachment],
    ]:
        message = Parser(
            policy=policy.default
        ).parsestr(
            (
                "Content-Type: multipart/mixed; "
                f'boundary="{boundary}"\n'
                "\n"
                f"{body}"
            )
        )

        if not message.is_multipart():
            raise ValueError(
                "Invalid multipart body"
            )

        text = None
        attachments = []

        for part in message.iter_parts():
            if (
                part.get_content_type()
                == "text/plain"
                and part.get_content_disposition()
                != "attachment"
            ):
                content = part.get_content()

                if isinstance(
                    content,
                    str,
                ):
                    text = content.strip()

                continue

            if (
                part.get_content_disposition()
                != "attachment"
            ):
                continue

            filename = part.get_filename()

            if filename is None:
                raise ValueError(
                    "Attachment has no filename"
                )

            content = part.get_payload(
                decode=True
            )

            if content is None:
                raise ValueError(
                    "Attachment has no content"
                )

            attachments.append(
                MimeAttachment(
                    filename=filename,
                    declared_mime=(
                        part.get_content_type()
                    ),
                    content=content,
                )
            )

        if text is None:
            raise ValueError(
                "Multipart body has no text/plain part"
            )

        return text, attachments
