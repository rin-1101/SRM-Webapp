from pathlib import Path
from datetime import datetime, timedelta
import yaml


class RaffleControl:

    def __init__(self):

        self.base_path = Path(__file__).parent
        self.config_path = self.base_path / "config"

    def load_setup(self):

        yaml_path = self.config_path / "setup.yaml"

        if not yaml_path.exists():
            raise FileNotFoundError(
                f"setup.yaml not found: {yaml_path}"
            )

        with open(yaml_path, "r") as file:

            data = yaml.safe_load(file)

        if data is None:
            raise ValueError(
                "setup.yaml is empty"
            )

        return data

    def load_event_config(self, event_name):

        yaml_path = self.config_path / f"{event_name}.yaml"

        if not yaml_path.exists():
            raise FileNotFoundError(
                f"Config file not found: {yaml_path}"
            )

        with open(yaml_path, "r") as file:
            return yaml.safe_load(file)

    def get_default_event(self):

        setup = self.load_setup()

        events = setup.get("events", [])

        if not events:
            raise ValueError(
                "No events found in setup.yaml"
            )

        return events[0]

    def get_dropdown_options(self):

        setup = self.load_setup()

        events = setup.get("events", [])

        options = []

        for event_name in events:

            config = self.load_event_config(event_name)

            options.append({
                "label": config["display_name"],
                "value": config["event_name"]
            })

        return options

    def get_time_options(self, event_name):

        config = self.load_event_config(event_name)

        return config.get("times", [])

    def get_prize_options(self, event_name):

        config = self.load_event_config(event_name)

        prize_config = config.get("prize", {})

        start = prize_config.get("start", 0)
        end = prize_config.get("end", 0)
        increment = prize_config.get("increment", 1)
        label = prize_config.get("label", "")
        extras = prize_config.get("extras", [])      # new

        options = []
        current = start

        while current <= end:

            value_str = f"{current:,}"
            display = f"{label} {value_str}" if label else value_str

            options.append({
                "label": display,
                "value": current
            })

            current += increment

        for item in extras:                           # new
            options.append({
                "label": item,
                "value": item
            })

        return options

    def get_date_options(self, event_name):

        config = self.load_event_config(event_name)

        date_config = config.get("dates", {})

        start_date = datetime.strptime(
            date_config["start"],
            "%Y-%m-%d"
        )

        end_date = datetime.strptime(
            date_config["end"],
            "%Y-%m-%d"
        )

        frequency_days = date_config.get(
            "frequency_days",
            7
        )

        options = []

        current_date = start_date

        while current_date <= end_date:

            formatted_date = (
                current_date
                .strftime("%B %d, %Y")
                .replace(" 0", " ")
                .upper()
            )

            options.append({
                "label": formatted_date,
                "value": formatted_date
            })

            current_date += timedelta(
                days=frequency_days
            )

        return options

    def get_message(self, event_name, key):

        config = self.load_event_config(event_name)

        messages = config.get("messages", {})

        return messages.get(key, "")

    def get_event_config(self, event_name):

        return self.load_event_config(event_name)

    def get_event_display_name(self, event_name):

        config = self.load_event_config(event_name)

        return config.get(
            "display_name",
            event_name
        )

    def get_event_dates(self, event_name):

        config = self.load_event_config(event_name)

        return config.get("dates", {})

    def get_event_prize_config(self, event_name):

        config = self.load_event_config(event_name)

        return config.get("prize", {})

    def get_event_times(self, event_name):

        config = self.load_event_config(event_name)

        return config.get("times", [])

    def validate_event(self, event_name):

        setup = self.load_setup()

        events = setup.get("events", [])

        return event_name in events

    def reload_config(self, event_name):

        return self.load_event_config(event_name)