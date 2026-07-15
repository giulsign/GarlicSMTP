from pathlib import Path
import tomllib


from garlicsmtp.exceptions import ConfigurationError


class Config:

    def __init__(self, filename="config/default.toml"):

        self.filename = Path(filename)

        if not self.filename.exists():
            raise ConfigurationError(f"Configuration file not found: {self.filename}")

        with self.filename.open("rb") as fp:
            self.data = tomllib.load(fp)

    def get(self, section, key=None):

        if key is None:
            return self.data.get(section)

        return self.data.get(section, {}).get(key)

    def __getitem__(self, item):
        return self.data[item]

    def __contains__(self, item):
        return item in self.data
