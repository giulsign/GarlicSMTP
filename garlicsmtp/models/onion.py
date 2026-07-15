from dataclasses import dataclass


@dataclass(slots=True)
class OnionAddress:
    localpart: str
    hostname: str

    @classmethod
    def parse(cls, address: str):
        localpart, hostname = address.split("@", 1)

        return cls(
            localpart=localpart,
            hostname=hostname.lower(),
        )

    @property
    def is_onion(self) -> bool:
        return self.hostname.endswith(".onion")

    @property
    def is_valid(self) -> bool:
        if not self.is_onion:
            return False

        label = self.hostname[:-6]

        return (
            len(label) == 56
            and label.isalnum()
        )

    def __str__(self) -> str:
        return f"{self.localpart}@{self.hostname}"