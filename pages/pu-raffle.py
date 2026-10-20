import logging
import sys
from pathlib import Path

import dash

PAGES_ROOT = Path(__file__).resolve().parent
if str(PAGES_ROOT) not in sys.path:
    sys.path.append(str(PAGES_ROOT))

from templates.simple_raffle import SimpleRaffleConfig
from templates.limited_raffle import LimitedRafflePage
from utils.login_handler import require_login, restricted_page
from utils.paths import PROFILE_UPDATE_RAFFLE


config = SimpleRaffleConfig(
    suffix="pu-raffle",
    page_path=PROFILE_UPDATE_RAFFLE,
    access_level=restricted_page[PROFILE_UPDATE_RAFFLE]["access_level"],
    entries_csv_path=PAGES_ROOT.parent / "documents" / "pu_raffle.csv",
    history_file_path=(
        PAGES_ROOT.parent
        / "JSON"
        / "raffle"
        / "winner_history"
        / "pu-winners.json"
    ),
    event_name="pu_raffle",
    title="Profile Update Raffle",
    button_label="Draw Raffle",
    initial_message="Press Draw Raffle to draw all 5 Deluxe Room Stay winners.",
    prize_enabled=True,
    prize_options_path=PAGES_ROOT.parent / "config" / "pu_prize.yaml",
    export_enabled=True,
    logger=logging.getLogger("pu-raffle"),
)

dash.register_page(__name__, path=config.page_path, name="Profile Update Raffle")
require_login(__name__, access_level=config.access_level)

page = LimitedRafflePage(config, prize_pool="PU")
layout = page.layout
page.register_callbacks()
