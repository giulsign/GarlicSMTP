class GarlicSMTP:

    def __init__(self, runtime):
        self.runtime = runtime

    def start(self) -> None:
        self.runtime.start()

    def run(self) -> None:
        self.runtime.run()

    def stop(self) -> None:
        self.runtime.stop()