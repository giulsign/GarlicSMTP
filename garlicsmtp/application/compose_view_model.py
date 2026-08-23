class ComposeViewModel:

    def __init__(
        self,
        composer,
    ) -> None:
        self.composer = composer

        self.sender = ""
        self.recipient = ""
        self.subject = ""
        self.body = ""

    def send(
        self,
    ) -> bool:
        result = self.composer.send(
            sender=self.sender,
            recipient=self.recipient,
            subject=self.subject,
            body=self.body,
        )

        if result:
            self.clear()

        return result

    def clear(
        self,
    ) -> None:
        self.sender = ""
        self.recipient = ""
        self.subject = ""
        self.body = ""