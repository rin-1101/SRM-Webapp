import random
import string
from decimal import Decimal, InvalidOperation
from pathlib import Path
from threading import Lock

import pandas as pd

from .state import WinnerSetState


def parse_entry_count(value, column, allow_blank=False):
    """Accept whole-number counts; missing consumed counts mean zero."""
    text = "" if value is None else str(value).strip()
    if allow_blank and not text:
        return 0
    try:
        count = Decimal(text)
    except InvalidOperation:
        raise ValueError(f"{column} must contain non-negative whole numbers") from None
    if not count.is_finite() or count < 0 or count != count.to_integral_value():
        raise ValueError(f"{column} must contain non-negative whole numbers")
    return int(count)


class Raffle:
    """Weighted raffle with persistent tickets and unique winner sets."""

    def __init__(self, data_path=None, winner_sets=None):
        reports_root = Path(__file__).resolve().parents[4]
        self.data_path = Path(data_path) if data_path else reports_root / "documents"
        self.winner_sets = winner_sets or WinnerSetState()
        self._draw_lock = Lock()

    def _event_path(self, event_name):
        return self.data_path / f"{event_name}.csv"

    def load_event_data(self, event_name):
        file_path = self._event_path(event_name)
        if not file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        data = pd.read_csv(file_path)
        required = {"Entries", "UniversalPlayerID", "Name"}
        missing = required.difference(data.columns)
        if missing:
            raise ValueError(f"CSV is missing required columns: {', '.join(sorted(missing))}")

        data["UniversalPlayerID"] = data["UniversalPlayerID"].astype(str).str.strip()
        data["Name"] = data["Name"].astype(str).str.strip()

        if "won_entries" not in data.columns:
            data["won_entries"] = 0

        for column in ("Entries", "won_entries"):
            values = data[column]
            if column == "won_entries":
                values = values.fillna(0)
            data[column] = values.map(lambda value: parse_entry_count(
                value, column, allow_blank=(column == "won_entries")
            )).astype(int)

        if (data["won_entries"] > data["Entries"]).any():
            raise ValueError("won_entries cannot be greater than Entries")

        data["remaining_entries"] = data["Entries"] - data["won_entries"]
        return data

    def draw(self, event_name):
        """Draw one ticket from a player who has not won in the active set."""
        with self._draw_lock:
            data = self.load_event_data(event_name)
            winner_ids = self.winner_sets.winner_ids(event_name)
            eligible = data[
                (data["remaining_entries"] > 0)
                & (~data["UniversalPlayerID"].isin(winner_ids))
            ]
            if eligible.empty:
                return None, None

            winner_index = eligible.sample(
                n=1,
                weights="remaining_entries",
            ).index[0]
            data.loc[winner_index, "won_entries"] += 1

            event_path = self._event_path(event_name)
            temp_path = event_path.with_suffix(".csv.tmp")
            data.drop(columns="remaining_entries").to_csv(temp_path, index=False)
            temp_path.replace(event_path)

            winner = data.loc[winner_index]
            self.winner_sets.add(
                event_name,
                winner["UniversalPlayerID"],
                winner["Name"],
            )
            return winner["UniversalPlayerID"], winner["Name"]

    def start_new_set(self, event_name):
        """Clear set uniqueness without restoring consumed entries."""
        with self._draw_lock:
            self.winner_sets.clear(event_name)

    def reset_entries(self, event_name):
        """Restore every ticket and clear the active winner set."""
        with self._draw_lock:
            data = self.load_event_data(event_name)
            data["won_entries"] = 0

            event_path = self._event_path(event_name)
            temp_path = event_path.with_suffix(".csv.tmp")
            data.drop(columns="remaining_entries").to_csv(temp_path, index=False)
            temp_path.replace(event_path)
            self.winner_sets.clear(event_name)

            total = int(data["Entries"].sum())
            return {
                "total": total,
                "used": 0,
                "remaining": total,
                "set_winners": 0,
            }

    def current_set_winners(self, event_name):
        records = self.winner_sets.get(event_name)
        columns = [
            "draw_number",
            "UniversalPlayerID",
            "Name",
            "won_entries",
            "remaining_entries",
            "drawn_at",
        ]
        if not records:
            return pd.DataFrame(columns=columns)

        winners = pd.DataFrame(records).rename(columns={
            "uid": "UniversalPlayerID",
            "name": "Name",
        })
        balances = self.load_event_data(event_name)[
            ["UniversalPlayerID", "won_entries", "remaining_entries"]
        ]
        winners = winners.merge(
            balances,
            on="UniversalPlayerID",
            how="left",
        )
        return winners[columns]

    def previous_winners(self, event_name):
        return self.current_set_winners(event_name)

    def entry_summary(self, event_name):
        data = self.load_event_data(event_name)
        return {
            "total": int(data["Entries"].sum()),
            "used": int(data["won_entries"].sum()),
            "remaining": int(data["remaining_entries"].sum()),
            "set_winners": len(self.winner_sets.get(event_name)),
        }

    @staticmethod
    def animation_value():
        random_code = "OM000" + "".join(random.choices(string.digits, k=6))
        return random_code, "*"
