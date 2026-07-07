# scripts/guess.py
import os
import random
import string
import pandas as pd

class Raffle:
    def __init__(self):
        self.om = "0"
        self.initials = "N.A."
        self.sm_path = "\\\\ominfstdpsd10001p-fs\\Casino\\Strategic Marketing\\Marketing Analysis\\Campaigns\\2511\\Win It Wednesday Raffle\\Raffle"

    def raffle_draw(self):
        file_name = f"Win It Wednesday Participants.csv"
        sm_file_path1 = os.path.join(self.sm_path, file_name)
        data = pd.read_csv(sm_file_path1)

        expanded_players = data.loc[data.index.repeat(data['Entries'])].reset_index(drop=True).drop(columns=['Entries'])
        expanded_players.head(2)
        winner = expanded_players.sample(n=1).iloc[0]
        # return winner['UniversalPlayerID'], winner['Name']
        return "OM000001738", "R.T."

    def raffle_animation(self):
        random_code = 'OM000' + ''.join(random.choices(string.digits, k=6))
        

        return random_code, "*"
