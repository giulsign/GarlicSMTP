# Copyright (c) 2026 Giuliano Signorelli
# SPDX-License-Identifier: LicenseRef-PolyForm-Noncommercial-1.0.0
#
# See LICENSE for the full license terms.

import json
from dataclasses import asdict
from datetime import datetime

from garlicsmtp.queue.item import (
    QueueItem
)
from garlicsmtp.storage.serializer import (
    MessageSerializer,
)


class QueueSerializer:

    @staticmethod
    def to_dict(
        item: QueueItem,
    ) -> dict:
        data = asdict(item)

        data["created"] = (
            item.created.isoformat()
        )

        data["message"] = (
            MessageSerializer.to_dict(
                item.message
            )
        )

        data["attempts"] = item.attempts

        data["next_retry"] = (
            item.next_retry.isoformat()
            if item.next_retry
            else None
        )

        data["last_error"] = item.last_error

        return data

    @staticmethod
    def to_json(
        item: QueueItem,
    ) -> str:
        return json.dumps(
            QueueSerializer.to_dict(item),
            indent=4,
            ensure_ascii=False,
        )

    @staticmethod
    def from_dict(
        data: dict,
    ) -> QueueItem:
        message = (
            MessageSerializer.from_dict(
                data["message"]
            )
        )

        return QueueItem(
            id=data["id"],
            created=datetime.fromisoformat(
                data["created"]
            ),
            message=message,
            attempts=data.get(
                "attempts",
                0,
            ),
            next_retry=(
                datetime.fromisoformat(
                    data["next_retry"]
                )
                if data.get("next_retry")
                else None
            ),
            last_error=data.get(
                "last_error"
            ),
        )

    @staticmethod
    def from_json(
        text: str,
    ) -> QueueItem:
        return QueueSerializer.from_dict(
            json.loads(text)
        )