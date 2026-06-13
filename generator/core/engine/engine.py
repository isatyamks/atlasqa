from .dataset import generator
from datetime import timedelta


class SimulationEngine:
    def __init__(self, config):
        self.config = config
        self.generator = generator()
        self.current_date = config.start_date

    def advance_time(self, delta_days: int):
        self.current_date += timedelta(days=delta_days)
        if self.current_date > self.config.end_date:
            self.current_date = self.config.end_date

    def get_random_employee(self):
        import random

        if not self.generator.employees:
            return None
        return random.choice(self.generator.employees)

    def get_random_service(self):
        import random

        if not self.generator.services:
            return None
        return random.choice(self.generator.services)
