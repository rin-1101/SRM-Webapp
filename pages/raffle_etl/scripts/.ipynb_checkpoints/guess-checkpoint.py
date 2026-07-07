# scripts/guess.py
import os
import json
from .initialize import Initialize  # Import Initialize class

class Guess:
    def __init__(self,  data_dir, file_utils, date_utils, init):
        self.data_dir = data_dir 
        self.file_utils = file_utils
        self.date_utils = date_utils
        self.init = init

    def guess_number(self, guess, test_code = None):
        if test_code:
            code = test_code
        else :
            code = self.file_utils.read_codes_from_files()
        
        if str(code['last_guess']) == str(self.date_utils.get_gaming_date()): 
            return False
        
        if not (isinstance(guess, str) and len(guess) == 7 and len(set(guess)) == 7 and guess.isdigit()):
            print("Guess must be a unique 7-digit number.")
            return False

        if str(guess) == str(code["code"]):
            # If the guess is correct
            code["guessed"] = True
            code["date_guessed"] = str(self.date_utils.get_gaming_date())
            # archive
            self.file_utils.write_code_to_file(code,os.path.join(self.data_dir, f"{self.date_utils.get_adjusted_week_number()}\\Archive"), f"code-{self.date_utils.now.strftime("%y-%m-%d_%H-%M-%S")}.json")
            
            print(f"Correct! Code guessed on {self.date_utils.get_gaming_date()}.")
            self.generate_new_code()

            return True
        else:
            print(f"Incorrect guess ({guess}).")
            return False

    def generate_new_code(self):
        """Generates a new code for the next week."""
        self.init.generate_code_file(last_guess = self.date_utils.get_gaming_date())
        print(f"New code initialized for the next week.")
