from datetime import datetime, timedelta
from pathlib import Path

import yaml


class RaffleControl:
    def __init__(self, config_path=None):
        self.config_path = (
            Path(config_path)
            if config_path
            else Path(__file__).resolve().parent / "config"
        )

    def load_setup(self):
        yaml_path = self.config_path / "setup.yaml"
        if not yaml_path.exists():
            raise FileNotFoundError(f"setup.yaml not found: {yaml_path}")

        with yaml_path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
        if not data:
            raise ValueError("setup.yaml is empty")
        return data

    def load_event_config(self, event_name):
        yaml_path = self.config_path / f"{event_name}.yaml"
        if not yaml_path.exists():
            raise FileNotFoundError(f"Config file not found: {yaml_path}")
        with yaml_path.open("r", encoding="utf-8") as file:
            return yaml.safe_load(file) or {}

    def get_default_event(self):
        events = self.load_setup().get("events", [])
        if not events:
            raise ValueError("No events found in setup.yaml")
        return events[0]

    def get_dropdown_options(self):
        return [
            {
                "label": self.load_event_config(event)["display_name"],
                "value": event,
            }
            for event in self.load_setup().get("events", [])
        ]

    def get_time_options(self, event_name):
        return self.load_event_config(event_name).get("times", [])

    def get_prize_options(self, event_name):
        config = self.load_event_config(event_name).get("prize", {})
        start = config.get("start", 0)
        end = config.get("end", 0)
        increment = config.get("increment", 1)
        label = config.get("label", "")
        extras = config.get("extras", [])

        options = []
        current = start
        while current <= end:
            value = f"{current:,}"
            options.append({
                "label": f"{label} {value}" if label else value,
                "value": current,
            })
            current += increment

        options.extend({"label": item, "value": item} for item in extras)
        return options

    def get_date_options(self, event_name):
        config = self.load_event_config(event_name).get("dates", {})
        current = datetime.strptime(config["start"], "%Y-%m-%d")
        end = datetime.strptime(config["end"], "%Y-%m-%d")
        step = timedelta(days=config.get("frequency_days", 7))

        options = []
        while current <= end:
            value = current.strftime("%B %d, %Y").replace(" 0", " ").upper()
            options.append({"label": value, "value": value})
            current += step
        return options

    def get_message(self, event_name, key):
        messages = self.load_event_config(event_name).get("messages", {})
        return messages.get(key, "")
