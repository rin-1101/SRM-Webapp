# scripts/date_utils.py
from datetime import datetime, timedelta

class DateUtils:
    def __init__(self):
        self.now = datetime.now()
        self.set_gaming_date() 
        self.set_week_number() 

    def set_time(self, time):
        self.now = time
        self.set_gaming_date()  
        self.set_week_number() 

    def set_gaming_date(self):
        if self.now.hour < 6:
            self.gaming_date = self.now - timedelta(days=1)
        else:
            self.gaming_date = self.now.date()

    def set_week_number(self):
        if hasattr(self, 'gaming_date'):  
            self.week_number = self.gaming_date.isocalendar()[1]
        else:
            self.week_number = self.now.isocalendar()[1]  

    def get_gaming_date(self):
        return self.gaming_date

    def get_adjusted_week_number(self):
        return self.week_number

    def get_now(self):
        return self.now
