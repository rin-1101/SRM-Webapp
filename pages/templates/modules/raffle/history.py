from datetime import datetime
from pathlib import Path


class RaffleHistory:
    def __init__(self, history_path=None):
        reports_root = Path(__file__).resolve().parents[4]
        self.history_path = (
            Path(history_path)
            if history_path
            else reports_root / "JSON" / "raffle"
        )

    def write(self, data):
        self.history_path.mkdir(parents=True, exist_ok=True)
        file_name = f"result-{datetime.now():%y%m%d %H%M%S %f}.csv"
        data.to_csv(self.history_path / file_name, index=False)
