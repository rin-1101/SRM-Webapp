import json
from datetime import datetime
from pathlib import Path


DEFAULT_STATE = {
    "uid": "Event is About to Begin",
    "initials": "-",
    "time": "-",
    "date": "-",
    "prize": "-",
    "animation_timestamp": 0,
}


class RaffleState:
    def __init__(self, state_path=None):
        self.state_path = Path(state_path) if state_path else Path.cwd()

    def _path(self, event_name):
        return self.state_path / f"{event_name}.json"

    def get(self, event_name):
        path = self._path(event_name)
        if not path.exists():
            self.save(DEFAULT_STATE.copy(), event_name)
            return DEFAULT_STATE.copy()

        with path.open("r", encoding="utf-8") as file:
            state = DEFAULT_STATE.copy()
            state.update(json.load(file))
            return state

    def save(self, data, event_name):
        self.state_path.mkdir(parents=True, exist_ok=True)
        path = self._path(event_name)
        temp_path = path.with_suffix(".json.tmp")
        with temp_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)
        temp_path.replace(path)


class WinnerSetState:
    """Persist the unique winners belonging to each event's active set."""

    def __init__(self, state_path=None):
        reports_root = Path(__file__).resolve().parents[4]
        self.state_path = (
            Path(state_path)
            if state_path
            else reports_root / "JSON" / "raffle" / "winner_sets"
        )

    def _path(self, event_name):
        return self.state_path / f"{event_name}.json"

    def get(self, event_name):
        path = self._path(event_name)
        if not path.exists():
            return []

        with path.open("r", encoding="utf-8") as file:
            winners = json.load(file)
        if not isinstance(winners, list):
            raise ValueError(f"Invalid winner set data: {path}")
        return winners

    def save(self, winners, event_name):
        self.state_path.mkdir(parents=True, exist_ok=True)
        path = self._path(event_name)
        temp_path = path.with_suffix(".json.tmp")
        with temp_path.open("w", encoding="utf-8") as file:
            json.dump(winners, file, indent=4)
        temp_path.replace(path)

    def add(self, event_name, uid, name):
        winners = self.get(event_name)
        winners.append({
            "draw_number": len(winners) + 1,
            "uid": str(uid),
            "name": str(name),
            "drawn_at": datetime.now().isoformat(timespec="seconds"),
        })
        self.save(winners, event_name)

    def clear(self, event_name):
        self.save([], event_name)

    def winner_ids(self, event_name):
        return {str(winner["uid"]) for winner in self.get(event_name)}


_default_state = RaffleState()


def get_data(event_name):
    return _default_state.get(event_name)


def save_data(data, event_name):
    _default_state.save(data, event_name)
