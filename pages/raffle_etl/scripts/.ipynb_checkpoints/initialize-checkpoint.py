import random
import os
from datetime import datetime, timedelta

class Initialize:
    def __init__(self, data_dir, file_utils, date_utils): #
        self.data_dir = data_dir
        self.date_utils = date_utils
        self.file_utils = file_utils

        self.initialize_code()

    def initialize_code(self):
        week_file = os.path.join(self.data_dir, f"{self.date_utils.get_adjusted_week_number()}/code.json")
        if os.path.exists(week_file):
            print(f"Week {self.date_utils.get_adjusted_week_number()} file already exists. Skipping initialization.")
            return 
        self.generate_code_file()

    def generate_unique_code(self):
        digits = list(range(10))
        random.shuffle(digits)
        return ''.join(str(d) for d in digits[:7])

    def generate_reveal_order(self, code_length=7):
        order = list(range(code_length))
        random.shuffle(order)
        return ','.join(str(i) for i in order)

    def generate_code_file(self, last_guess = None):
        code = self.generate_unique_code()
        reveal_order = self.generate_reveal_order(len(code))
        
        # Assuming self.date_utils.get_gaming_date() returns the current date
        current_date = self.date_utils.get_gaming_date()

        # Calculate Monday of the current week
        monday_this_week = current_date - timedelta(days=current_date.weekday())

        # Format the date to string (you can adjust the format as needed)
        date_added = monday_this_week.strftime('%Y-%m-%d')
        week_data = {
            "id": 1,
            "code": code,
            "reveal_order": reveal_order,
            "revealed_indices": [],
            "active": True,
            "guessed": False,
            "date_added": date_added,  # Monday of this week
            "week": self.date_utils.get_adjusted_week_number(),
            "last_guess": str(last_guess),
        }
        # Write the week data to the JSON file
        
        self.file_utils.write_code_to_file(week_data, self.data_dir,  f"{self.date_utils.get_adjusted_week_number()}/code.json")
        print(f"Week file for week {self.date_utils.get_adjusted_week_number()} created successfully.")