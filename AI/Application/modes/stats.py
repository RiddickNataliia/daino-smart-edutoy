import json
import os

class StatsManager:
    def __init__(self, stats_file='stats.json'):
        self.stats_file = stats_file
        self.stats = self.load_stats()

    def load_stats(self):
        if os.path.exists(self.stats_file):
            with open(self.stats_file, 'r') as f:
                return json.load(f)
        return {}

    def record(self, mode, stat, value):
        if mode not in self.stats:
            self.stats[mode] = {}
        self.stats[mode][stat] = value
        self.save_stats()

    def get_stats(self, mode):
        return self.stats.get(mode, {})

    def save_stats(self):
        with open(self.stats_file, 'w') as f:
            json.dump(self.stats, f, indent=2)
