from garlicsmtp.models import OnionAddress


class OnionValidator:

    def resolve(self, recipient: str) -> OnionAddress:
        address = OnionAddress.parse(recipient)

        if not address.is_valid:
            raise ValueError(
                f"Invalid onion address: {recipient}"
            )

        return address