# ctc.py
from .scripts.date_utils import DateUtils
from .scripts.file_utils import FileUtils
from .scripts.raffle import Raffle
from datetime import datetime


class Raffle_app:
    def __init__(self):
        self.date_utils = DateUtils()  
        self.file_utils = FileUtils(self.date_utils)
        self.raffle = Raffle()

    def draw(self, event_name):
        return self.raffle.raffle_draw(event_name)

    def draw_animate(self):
        return self.raffle.raffle_animation()
    def write_draw(self,data):
        self.file_utils.write_draw(data)