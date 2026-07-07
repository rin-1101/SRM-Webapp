import os
import json
import pandas as pd
import glob
from datetime import datetime, timedelta

class GuessHistory:
    def __init__(self, path, db_dir="guess-history", user="system"):
        """
        Initialize the GuessHistory class. Creates the necessary directories for storing individual guess files.
        """
        self.log_path = os.path.join(path, "logs.json")

        self.db_dir = os.path.join(path, db_dir)  
        self.user = user

        # Ensure the directory for guesses exists
        os.makedirs(self.db_dir, exist_ok=True)


    def get_gaming_date(self):
        """
        Returns the gaming date based on a 6 AM cutoff.
        If it's before 6 AM, the gaming date is the previous day.
        """
        now = datetime.now()
        if now.hour < 6:
            now -= timedelta(days=1)
        gaming_date = now.replace(hour=6, minute=0, second=0, microsecond=0)
        return gaming_date.strftime("%Y-%m-%d")

    def add_guess(self, path, uid, guess, code, correct=False, week=None):
        """
        Add a new guess entry for a player.
        Prevent duplicates within 6 seconds.
        Automatically determines week and calculates attempts for the day.
        """
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        result = "correct" if correct else "incorrect"
        week = week or now.isocalendar()[1]

        # Get the gaming date based on the 6 AM cutoff
        gaming_date = self.get_gaming_date()

        # Create the directory for the gaming date if it doesn't exist
        gaming_date_folder = os.path.join(self.db_dir, gaming_date)
        os.makedirs(gaming_date_folder, exist_ok=True)

        # The filename for the guess
        guess_file_name = f"{uid}_{timestamp.replace(':', '-')}_{result}.json"
        guess_file_path = os.path.join(gaming_date_folder, guess_file_name)

        # Check if the guess already exists within 6 seconds
        if os.path.exists(guess_file_path):
            with open(guess_file_path, 'r') as f:
                existing_guess = json.load(f)
                existing_time = datetime.strptime(existing_guess['time_submitted'], "%Y-%m-%d %H:%M:%S")
                duration = (now - existing_time).total_seconds()
                if duration <= 6:
                    return "Duplicate guess detected within 6 seconds, try again later."

        # Prepare the new guess entry
        new_guess = {
            "uid": uid,
            "date_guessed": date_str,
            "guess": guess,
            "code": code,
            "result": result,
            "week": week,
            "time_submitted": timestamp,
            "attempts": 1,  # This can be adjusted if you need to calculate attempts
            "duration_since_last": 0  # This can be adjusted as needed
        }

        # Save the guess as a separate JSON file in the correct folder
        with open(guess_file_path, 'w') as guess_file:
            json.dump(new_guess, guess_file)
        return True


    # ==========================================================
    # ✅ FETCH / SEARCH
    # ==========================================================
    def get_all_guesses(self):
        try:
            guesses = []
            for filename in os.listdir(self.db_dir):
                if filename.endswith(".json"):  # Check if the file is a JSON file
                    with open(os.path.join(self.db_dir, filename), 'r') as guess_file:
                        guess = json.load(guess_file)
                        guesses.append(guess)
            return guesses
        except Exception as e:
            return []

    def get_user_history(self, uid):
        try:
            user_guesses = []
            for filename in os.listdir(self.db_dir):
                if filename.endswith(".json"):
                    with open(os.path.join(self.db_dir, filename), 'r') as guess_file:
                        guess = json.load(guess_file)
                        if guess['uid'] == uid:
                            user_guesses.append(guess)
            return user_guesses
        except Exception as e:
            return []

    def search(self, uid=None, gaming_date=None):
        try:
            guesses = []
            print(f"Searching in directory: {self.db_dir} for gaming date: {gaming_date}")
            gaming_date_folder = os.path.join(self.db_dir, gaming_date)
            os.makedirs(gaming_date_folder, exist_ok=True)
            if not os.path.exists(gaming_date_folder):
                print(f"Gaming date folder {gaming_date_folder} does not exist.")
                return pd.DataFrame()  # Return an empty DataFrame if folder doesn't exist

            search_pattern = os.path.join(gaming_date_folder, f"{uid if uid else ''}*.json")
            json_files = glob.glob(search_pattern)

            # Loop through all matching JSON files
            for file_path in json_files:
                with open(file_path, 'r') as guess_file:
                    guess = json.load(guess_file)
                    print(f"Reading file: {file_path}, Guess: {guess}")
                    
                    # Append the guess to the list if it matches the UID (if provided)
                    if not uid or guess['uid'] == uid:
                        guesses.append(guess)

            # Convert the list of guesses to a DataFrame and return it
            if guesses:
                df = pd.DataFrame(guesses)
            else:
                df = pd.DataFrame()

            return df
        
        except Exception as e:
            print(f"An error occurred: {e}")
            return pd.DataFrame()