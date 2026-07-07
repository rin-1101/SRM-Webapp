import os
import random
import string
import pandas as pd

class Raffle:
    def __init__(self):
        self.sm_path = r"\\ominfstdpsd10001p-fs\Casino\Strategic Marketing\Database Admin\ETL\Applications\reports\documents"
        self.previous_winners = set()  # Track winners to prevent duplicates

    def load_event_data(self, event_name):
        """Load CSV data for the event and expand based on entries."""
        file_name = f"{event_name}.csv"
        file_path = os.path.join(self.sm_path, file_name)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"CSV file not found: {file_path}")
        
        data = pd.read_csv(file_path)
        if 'Entries' not in data.columns or 'UniversalPlayerID' not in data.columns:
            raise ValueError("CSV must contain 'Entries' and 'UniversalPlayerID' columns")
        
        # Expand rows based on number of entries
        expanded_players = data.loc[data.index.repeat(data['Entries'])].reset_index(drop=True)
        return expanded_players

    def raffle_draw(self, event_name):
        """Draw a winner, ensuring no duplicates."""
        expanded_players = self.load_event_data(event_name)
        
        # Remove previous winners from the draw
        if self.previous_winners:
            expanded_players = expanded_players[~expanded_players['UniversalPlayerID'].isin(self.previous_winners)]
        
        if expanded_players.empty:
            return None, None  # No more eligible winners
        
        winner = expanded_players.sample(n=1).iloc[0]
        self.previous_winners.add(winner['UniversalPlayerID'])
        return winner['UniversalPlayerID'], winner['Name']

    def raffle_animation(self):
        """Generate a random raffle animation code."""
        random_code = 'OM000' + ''.join(random.choices(string.digits, k=6))
        return random_code, "*"