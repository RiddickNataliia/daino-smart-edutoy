class BaseMode:
    def __init__(self, stats_manager):
        self.stats = stats_manager

    def start(self):
        pass

    def process_frame(self, frame):
        pass

    def handle_event(self, event):
        pass

    def update(self):
        pass

    def render(self):
        pass

    def end(self):
        pass
