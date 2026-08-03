from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ApplicationPaths:

    root_dir: Path

    @classmethod
    def for_user(
        cls,
        home: Path | None = None,
    ) -> "ApplicationPaths":
        user_home = (
            home
            if home is not None
            else Path.home()
        )

        return cls(
            root_dir=(
                user_home
                / ".local"
                / "share"
                / "garlicsmtp"
            )
        )

    @property
    def config_dir(self) -> Path:
        return self.root_dir / "config"

    @property
    def data_dir(self) -> Path:
        return self.root_dir / "data"

    @property
    def state_dir(self) -> Path:
        return self.root_dir / "state"

    @property
    def cache_dir(self) -> Path:
        return self.root_dir / "cache"

    @property
    def log_dir(self) -> Path:
        return self.state_dir / "logs"

    @property
    def settings_file(self) -> Path:
        return self.config_dir / "settings.toml"

    @property
    def mailbox_database(self) -> Path:
        return self.data_dir / "mailboxes.db"

    @property
    def queue_database(self) -> Path:
        return self.state_dir / "queue.db"

    def create_directories(
        self,
    ) -> None:
        directories = (
            self.config_dir,
            self.data_dir,
            self.state_dir,
            self.cache_dir,
            self.log_dir,
        )

        for directory in directories:
            directory.mkdir(
                parents=True,
                exist_ok=True,
            )