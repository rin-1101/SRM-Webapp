import logging
import sys
from pathlib import Path

import dash

PAGES_ROOT = Path(__file__).resolve().parent
if str(PAGES_ROOT) not in sys.path:
    sys.path.append(str(PAGES_ROOT))

from templates.raffle_entries import (
    RaffleEntriesConfig,
    RaffleEntriesPage,
    saturday_raffle_entry_label,
)
from utils.login_handler import require_login, restricted_page
from utils.paths import HIGH_LIMIT_RAFFLE_CHECKER


ENTRIES_CSV_PATH = PAGES_ROOT.parent / "documents" / "snowball_mania.csv"

config = RaffleEntriesConfig(
    suffix="highlimit-raffle-checker",
    page_path=HIGH_LIMIT_RAFFLE_CHECKER,
    access_level=restricted_page[HIGH_LIMIT_RAFFLE_CHECKER]["access_level"],
    entries_csv_path=ENTRIES_CSV_PATH,
    title="HighLimit Raffle Checker",
    subtitle="Enter your patron ID to view your entitled raffle entries.",
    entry_label_provider=saturday_raffle_entry_label,
    logo_src="/assets/snowball/logo.png",
    background_src="/assets/snowball/bg.png",
    logger=logging.getLogger("highlimit-raffle-checker"),
)

dash.register_page(
    __name__,
    path=config.page_path,
    name="HighLimit Raffle Checker",
)
require_login(__name__, access_level=config.access_level)

page = RaffleEntriesPage(config)
layout = page.layout
page.register_callbacks()