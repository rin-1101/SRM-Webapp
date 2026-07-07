

import sys

import dash

ROOT = "\\\\ominfstdpsd10001p-fs.int.okadamanila.com\\Casino\\Strategic Marketing\\Database Admin\\ETL\\Applications\\okada"
sys.path.append(ROOT)

ROOT2 = "\\\\ominfstdpsd10001p-fs.int.okadamanila.com\\Casino\\Strategic Marketing\\Database Admin\\ETL\\Applications"
sys.path.append(f"{ROOT2}\\okada\\")
sys.path.append(f"{ROOT2}\\reports\\utils\\app_classes\\")

from utils.paths import DYSON_LUXE_REWARDS
from utils.login_handler import require_login, restricted_page
from templates.shopping import ShopConfig, ShoppingPage

PATH_DB       = r"\\ominfstdpsd10001p-fs.int.okadamanila.com\Casino\Strategic Marketing\Database Admin\ETL\Applications\reports\sqlite\inventory\dyson.db"
PATH_DATA     = r"\\ominfstdpsd10001p-fs.int.okadamanila.com\Casino\Strategic Marketing\Database Admin\ETL\Applications\reports\sqlite\shop"
PATH_INV      = r"\\ominfstdpsd10001p-fs.int.okadamanila.com\Casino\Strategic Marketing\Database Admin\ETL\Applications\reports\sqlite\inventory"
PATH_TIER_CSV = r"\\ominfstdpsd10001p-fs.int.okadamanila.com\Casino\Strategic Marketing\Marketing Analysis\Campaigns\2507\VIP Shopping Galore\etl\history\tier-snap.csv"

config = ShopConfig(
    suffix="dyson",
    page_path=DYSON_LUXE_REWARDS,
    access_level=restricted_page[DYSON_LUXE_REWARDS]["access_level"],

    path_db=PATH_DB,
    path_data=PATH_DATA,
    path_inv=PATH_INV,
    path_tier_csv=PATH_TIER_CSV,
    db_filename="dyson.db",

    assets_folder="dyson",
    css_prefix="dyson",            # keep existing /assets/dyson/style.css selectors working as-is

    max_per_category=3,
    campaign_start="2026-07-06 06:00:00",
    campaign_end="2026-07-07 05:59:00",
    redeemed_window_start="2026-07-06 06:00:00",
    redeemed_window_end="2026-07-07 06:00:00",
    valid_tier_ids=(7, 15, 10022),

    logger_name="direct-offer",

    # QA/dev override, same as the original hardcoded OM000000001 shortcut
    balance_overrides={"OM000000001": 50000},
)

# Register + auth directly at module top level, BEFORE instantiating the
# template — matches templates/raffle.py's working pattern (dash's page
# walker is happiest when register_page() runs in the file it's scanning).
dash.register_page(__name__, path=config.page_path)
require_login(__name__, access_level=config.access_level)

page = ShoppingPage(__name__, config)
layout = page.layout
page.register_callbacks()