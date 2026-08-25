from pathlib import Path


class OnionServiceManager:

    def __init__(
        self,
        *,
        client,
        authenticator=None,
        identity_file: Path,
        virtual_port: int,
        target_host: str,
        target_port: int,
        hostname_callback=None,
    ) -> None:
        self.client = client
        self.authenticator = authenticator
        self.identity_file = identity_file
        self.virtual_port = virtual_port
        self.target_host = target_host
        self.target_port = target_port
        self.hostname_callback = (
            hostname_callback
        )

        self.hostname: str | None = None

    def start(
        self,
    ) -> None:
        self.client.connect()

        if self.authenticator is not None:
            self.authenticator.authenticate()

        self.hostname = self.ensure_service()

        if self.hostname_callback is not None:
            self.hostname_callback(
                self.hostname
            )

    def stop(
        self,
    ) -> None:
        self.client.close()

    def ensure_service(
        self,
    ) -> str:
        if self.identity_file.exists():
            key = self.identity_file.read_text(
                encoding="utf-8"
            ).strip()
        else:
            key = "NEW:ED25519-V3"

        service = self.client.add_onion(
            key=key,
            virtual_port=self.virtual_port,
            target_host=self.target_host,
            target_port=self.target_port,
        )

        if key == "NEW:ED25519-V3":
            self.identity_file.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            self.identity_file.write_text(
                service.private_key,
                encoding="utf-8",
            )

        return (
            service.service_id
            + ".onion"
        )