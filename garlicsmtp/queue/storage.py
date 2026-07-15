from pathlib import Path

from garlicsmtp.queue.item import QueueItem
from garlicsmtp.queue.serializer import QueueSerializer


class QueueStorage:

    def __init__(self, directory: str | Path):

        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def save(self, item: QueueItem):

        filename = self.directory / f"{item.id}.json"

        filename.write_text(

            QueueSerializer.to_json(item),

            encoding="utf-8"

        )

    def load(self, item_id: str) -> QueueItem:

        filename = self.directory / f"{item_id}.json"

        return QueueSerializer.from_json(

            filename.read_text(

                encoding="utf-8"

            )

        )

    def delete(self, item_id: str):

        filename = self.directory / f"{item_id}.json"

        if filename.exists():

            filename.unlink()

    def exists(self, item_id: str) -> bool:

        return (self.directory / f"{item_id}.json").exists()

    def list(self):

        return sorted(self.directory.glob("*.json"))
