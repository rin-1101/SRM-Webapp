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
from utils.paths import ONE_MILLION_RAFFLE_KIOSK


config = SimpleRaffleConfig(
    suffix="1m-raffle-kiosk",
    page_path=ONE_MILLION_RAFFLE_KIOSK,
    access_level=restricted_page[ONE_MILLION_RAFFLE_KIOSK]["access_level"],
    entries_csv_path=PAGES_ROOT.parent / "documents" / "ooc1m_KIOSK.csv",
    history_file_path=(
        PAGES_ROOT.parent
        / "JSON"
        / "raffle"
        / "winner_history"
        / "ooc1m_KIOSK-winners.json"
    ),
    event_name="ooc1m_KIOSK",
    title="1M Raffle KIOSK",
    button_label="Draw Raffle",
    initial_message="Press Draw Raffle to draw all 10 prize winners.",
    prize_enabled=True,
    prize_options_path=PAGES_ROOT.parent / "config" / "1m_prize.yaml",
    export_enabled=True,
    logger=logging.getLogger("1m-raffle-kiosk"),
)

dash.register_page(__name__, path=config.page_path, name="1M Raffle KIOSK")
require_login(__name__, access_level=config.access_level)

page = LimitedRafflePage(config, prize_pool="KIOSK")
layout = page.layout
page.register_callbacks()
