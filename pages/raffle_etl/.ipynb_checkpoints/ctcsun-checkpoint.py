import sqlite3
import pandas as pd
import random
from datetime import datetime, timedelta

class SundayCodeGame:
    def __init__(self, db_path="sunday_codes.db"):
        self.db_path = db_path
        self._create_table()
        self._initialize_weekly_codes()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _create_table(self):
        """Create the table if it doesn't exist"""
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS codes (
                    code TEXT UNIQUE,
                    date_added TEXT,
                    week TEXT,
                    is_correct INTEGER,
                    player_guessed TEXT
                )
            """)
            conn.commit()

    def _get_current_week(self):
        """Return the ISO week of the year (Monday 6 AM to next Monday 6 AM)"""
        now = datetime.now()

        # Adjust so that before Monday 6 AM counts as part of the previous week
        if now.weekday() == 0 and now.hour < 6:
            now -= timedelta(days=1)

        # Determine ISO year and week number
        year, week_num, _ = now.isocalendar()
        return f"{week_num:02d}"


    def _initialize_weekly_codes(self):
        """Generate 5 codes per week if not already created"""
        week = self._get_current_week()
        with self._connect() as conn:
            existing = pd.read_sql("SELECT * FROM codes WHERE week = ?", conn, params=(week,))
            if not existing.empty:
                print(f"Codes already initialized for week {week}")
                return

            codes = []
            for _ in range(5):
                code = ''.join(str(n) for n in random.sample(range(10), 7))
                codes.append(code)

            correct_index = random.randint(0, 4)
            data = [
                (code, datetime.now().strftime("%Y-%m-%d"), week, int(i == correct_index), None)
                for i, code in enumerate(codes)
            ]
            conn.executemany("""
                INSERT INTO codes (code, date_added, week, is_correct, player_guessed)
                VALUES (?, ?, ?, ?, ?)
            """, data)
            conn.commit()
            print(f"Generated 5 new codes for week {week} (correct: {codes[correct_index]})")

    def read_codes(self):
        """Return all codes as a DataFrame"""
        with self._connect() as conn:
            df = pd.read_sql("SELECT * FROM codes", conn)
        return df

    def get_current_week_codes(self):
        """Return only this week’s codes"""
        week = self._get_current_week()
        with self._connect() as conn:
            df = pd.read_sql("SELECT * FROM codes WHERE week = ?", conn, params=(week,))
        return df

    def guess_number(self, player_id, number_guessed):
        """Player attempts to guess the weekly correct code"""
        week = self._get_current_week()
        with self._connect() as conn:
            df = pd.read_sql("SELECT * FROM codes WHERE week = ?", conn, params=(week,))

            if df.empty:
                print("No codes found for the current week.")
                return False

            correct_code_row = df[df["is_correct"] == 1].iloc[0]
            correct_code = correct_code_row["code"]
            player_already_won = not df[df["player_guessed"] == str(player_id)].empty

            if player_already_won:
                print(f"Player {player_id} has already guessed the correct code this week.")
                return False

            if str(number_guessed) == correct_code:
                conn.execute("""
                    UPDATE codes
                    SET player_guessed = ?
                    WHERE code = ? AND week = ?
                """, (player_id, correct_code, week))
                conn.commit()
                print(f"✅ Correct guess! Player {player_id} guessed the code {correct_code}.")
                return True
            else:
                print("❌ Incorrect guess.")
                return False

