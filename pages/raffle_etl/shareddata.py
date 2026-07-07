import json
import yaml

from pathlib import Path


BASE_DIR = Path(__file__).parent
CONFIG_DIR = BASE_DIR / "config"

SETUP_FILE = CONFIG_DIR / "setup.yaml"


def create_default_yaml(event_name):

    CONFIG_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    yaml_file = CONFIG_DIR / f"{event_name}.yaml"

    display_name = (
        event_name
        .replace("_", " ")
        .title()
    )

    default_yaml = {
        "event_name": event_name,

        "display_name": display_name,

        "times": [
            {
                "label": "10:00 PM",
                "value": "10_00 PM"
            }
        ],

        "prize": {
            "start": 10000,
            "end": 100000,
            "increment": 10000
        },

        "dates": {
            "start": "2026-06-01",
            "end": "2026-07-31",
            "frequency_days": 7
        },

        "messages": {
            "reset": "Draw is about to Begin",
            "next_draw": "Next Draw is at 10PM"
        }
    }

    with open(yaml_file, "w") as f:
        yaml.dump(
            default_yaml,
            f,
            sort_keys=False
        )

    update_setup_yaml(event_name)


def update_setup_yaml(event_name):

    CONFIG_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    if not SETUP_FILE.exists():

        setup_data = {
            "events": []
        }

    else:

        with open(SETUP_FILE, "r") as f:

            setup_data = yaml.safe_load(f)

        if setup_data is None:

            setup_data = {
                "events": []
            }

    if "events" not in setup_data:

        setup_data["events"] = []

    if event_name not in setup_data["events"]:

        setup_data["events"].append(event_name)

    with open(SETUP_FILE, "w") as f:

        yaml.dump(
            setup_data,
            f,
            sort_keys=False
        )


def get_data(event_name):

    DATA_FILE = Path(f"{event_name}.json")

    DEFAULT = {
        "uid": "Event is About to Begin",
        "initials": "-",
        "time": "-",
        "date": "-",
        "prize": "-"
    }

    yaml_file = CONFIG_DIR / f"{event_name}.yaml"

    if not yaml_file.exists():

        create_default_yaml(event_name)

    if DATA_FILE.exists():

        with open(DATA_FILE, 'r') as f:

            return json.load(f)

    with open(DATA_FILE, 'w') as f:

        json.dump(
            DEFAULT,
            f,
            indent=4
        )

    return DEFAULT


def save_data(data, event_name):

    DATA_FILE = Path(f"{event_name}.json")

    with open(DATA_FILE, 'w') as f:

        json.dump(
            data,
            f,
            indent=4
        )