from datetime import datetime, timedelta

class CodeReveal:
    def __init__(self, data_dir, file_utils, date_utils):
        self.file_utils = file_utils
        self.data_dir = data_dir
        self.date_utils = date_utils
#
    def get_revealed_number(self):
        code = self._get_code_from_file()
        # return code.get("code")
        if not code:
            print("No code data found.")
            return f"No code data found. | week : {self.date_utils.get_adjusted_week_number()} | filepath : {self.file_utils.week_folder}"

        try:
            start_date_str = code.get("date_added")
            if start_date_str in ["None", None, ""]:
                print(f"Invalid 'date_added' field: {start_date_str}. Setting to today's date.")
                start_date = self.date_utils.get_gaming_date()  # Use the current date
            else:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()  # Parse the date

        except Exception as e:
            print(f"Error parsing 'date_added': {e}")
            return "Error parsing 'date_added'."
        
        # Use the test_date if provided, otherwise use the current date
        today = self.date_utils.get_gaming_date()  # Use the passed date or the current date

        offset = 0  # Add logic if needed

        try:
            guessed_date = code.get("last_guess")
            if guessed_date != "None" and guessed_date is not None:
                print(f"Guessed date = {guessed_date}")

                if guessed_date == str(today):
                    print(f"Patron has already guessed today. No new code will be revealed.")
                    return "No reveal"

                start_date = datetime.strptime(guessed_date, "%Y-%m-%d").date()
                offset = -1

        except Exception as e:
            print(f"Error parsing 'last_guess': {e}")
            return "Error parsing 'last_guess'."

        try:
            # Calculate the number of days passed from the start date to today
            today_str = today.strftime('%Y-%m-%d')  # Format today as a string (YYYY-MM-DD)
            start_date_str = start_date.strftime('%Y-%m-%d')  # Format start_date as a string (YYYY-MM-DD)
            today = datetime.strptime(today_str, '%Y-%m-%d').date()
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            days_passed = (today - start_date).days + 1 + offset
        except Exception as e:
            print(f"Error calculating days passed: {e}")
            return f"Error calculating days passed. {e}"

        # If no days passed, return None (nothing to reveal)
        if days_passed < 1:
            print("No digits to reveal.")
            return "None"

        try:
            # Process reveal order and calculate which digits to reveal
            reveal_order_list = [int(i) for i in code["reveal_order"].split(',')]
            reveal_count = min(days_passed, len(reveal_order_list))
            revealed_indices = reveal_order_list[:reveal_count]

            revealed_digits = [code["code"][i] for i in revealed_indices]

            print(f"Revealed digits: {' '.join(revealed_digits)}")
            return ' '.join(revealed_digits)

        except KeyError as e:
            print(f"Missing key in code data: {e}")
            return f"Error: Missing key {e} in code data."

        except Exception as e:
            print(f"Error revealing digits: {e}")
            return "Error revealing digits."
    def _get_code_from_file(self):
        """Helper method to safely read code from files."""
        try:
            code = self.file_utils.read_codes_from_files()
            if not code:
                print("Code data is empty or not found.")
                return []
            return code
        except Exception as e:
            print(f"Error reading code from file: {e}")
            return None
