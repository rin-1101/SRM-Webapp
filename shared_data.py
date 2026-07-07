# import json
# from pathlib import Path

# DATA_FILE = Path("shared_state.json")

# def get_data():
#     if DATA_FILE.exists():
#         with open(DATA_FILE, 'r') as f:
#             return json.load(f)
#     return {
#         "uid": "OM0000679",
#         "initials": "R.T.",
#         "time": "12:00",
#         "date": "2025-17-38"
#     }

# def save_data(data):
#     with open(DATA_FILE, 'w') as f:
#         json.dump(data, f)