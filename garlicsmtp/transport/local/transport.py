from pathlib import Path

from garlicsmtp.queue.item import QueueItem
from garlicsmtp.queue.serializer import QueueSerializer
from garlicsmtp.transport.base import Transport


class LocalTransport(Transport):

    def __init__(self, spool_directory: str = "spool/outgoing"):

        self.directory = Path(spool_directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def deliver(self, item: QueueItem) -> bool:

        filename = self.directory / f"{item.id}.json"

        data = QueueSerializer.to_json(item)

        filename.write_text(
            data,
            encoding="utf-8",
        )

        return True