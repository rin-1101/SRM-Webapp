import os
import json
from datetime import datetime

class FileUtils:
    def __init__(self, data_dir, date_utils):
        self.data_dir = data_dir
        self.date_utils = date_utils
        self.update_folder_paths()  # Initialize folder paths on creation

    def update_folder_paths(self):
        """Recalculate the week folder and archive folder based on the current week."""
        week_number = self.date_utils.get_adjusted_week_number()  # Get the current week number
        self.week_folder = os.path.join(self.data_dir, str(week_number))
        self.archive_folder = os.path.join(self.week_folder, "Archive")
        os.makedirs(self.week_folder, exist_ok=True)
        os.makedirs(self.archive_folder, exist_ok=True)  # Ensure the archive folder exists

    def reset_folders_on_date_change(self):
        """Call this method when the date changes to update the folder paths."""
        self.update_folder_paths()



    def write_code_to_file(self, code_data, week_folder_path, filename):
        #checks if exists
        os.makedirs(week_folder_path, exist_ok=True)
        
        file_path = os.path.join(week_folder_path, filename)
        
        with open(file_path, 'w') as f:
            json.dump(code_data, f, indent=4)
            
        print(f"Code data written to file: {file_path}")

    def read_codes_from_files(self):
        """Read and return codes from files, sorted by ID in the desired pattern."""

        if not os.path.exists(self.week_folder):
            print(f"Directory does not exist: {self.week_folder}")
            return []
        try:
            with open(os.path.join(self.week_folder, "code.json"), 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Failed to read code : {e}")
        

