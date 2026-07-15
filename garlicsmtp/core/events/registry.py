class EventRegistry:

    def __init__(self):

        self.events = {}

    def register(self, event):

        self.events[event.__name__] = event

    def get(self, name):

        return self.events[name]
