from .draw import Raffle
from .history import RaffleHistory


class RaffleApp:
    """Small facade used by the control page and raffle display."""

    def __init__(self, raffle=None, history=None):
        self.raffle = raffle or Raffle()
        self.history = history or RaffleHistory()

    def draw(self, event_name):
        return self.raffle.draw(event_name)

    def draw_animate(self):
        return self.raffle.animation_value()

    def start_new_set(self, event_name):
        self.raffle.start_new_set(event_name)

    def reset_entries(self, event_name):
        return self.raffle.reset_entries(event_name)

    def get_current_set_winners(self, event_name):
        return self.raffle.current_set_winners(event_name)

    def get_previous_winners(self, event_name):
        return self.get_current_set_winners(event_name)

    def get_entry_summary(self, event_name):
        return self.raffle.entry_summary(event_name)

    def write_draw(self, data):
        self.history.write(data)


Raffle_app = RaffleApp
