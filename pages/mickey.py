"""Mickey TP shopping page."""

import sys
from pathlib import Path

import dash


PAGES_ROOT = Path(__file__).resolve().parent
if str(PAGES_ROOT) not in sys.path:
    sys.path.append(str(PAGES_ROOT))

ROOT = r"\\ominfstdpsd10001p-fs.int.okadamanila.com\Casino\Strategic Marketing\Database Admin\ETL\Applications\okada"
sys.path.append(ROOT)

ROOT2 = r"\\ominfstdpsd10001p-fs.int.okadamanila.com\Casino\Strategic Marketing\Database Admin\ETL\Applications"
sys.path.append(str(Path(ROOT2) / "okada"))
sys.path.append(str(Path(ROOT2) / "reports" / "utils" / "app_classes"))

from utils.paths import MICKEY
from utils.login_handler import require_login, restricted_page
from templates.shopping import ShopConfig, ShoppingPage


PATH_DB = str(Path(ROOT2) / "reports" / "sqlite" / "inventory" / "mickey.db")
PATH_DATA = str(Path(ROOT2) / "reports" / "sqlite" / "shop")
PATH_INV = str(Path(ROOT2) / "reports" / "sqlite" / "inventory")
PATH_TIER_CSV = r"\\ominfstdpsd10001p-fs.int.okadamanila.com\Casino\Strategic Marketing\Marketing Analysis\Campaigns\2611\Mickey\etl\history\tier-snap.csv"

CAMPAIGN_START = "2026-11-01 06:00:00"
CAMPAIGN_END = "2026-11-10 06:00:00"


config = ShopConfig(
    suffix="mickey",
    page_path=MICKEY,
    access_level=restricted_page[MICKEY]["access_level"],

    path_db=PATH_DB,
    path_data=PATH_DATA,
    path_inv=PATH_INV,
    path_tier_csv=PATH_TIER_CSV,
    db_filename="mickey.db",

    assets_folder="mickey",
    css_prefix="shop",
    logo="default",
    style_options=("base",),
    default_style="base",

    max_per_category=3,
    campaign_start=CAMPAIGN_START,
    campaign_end=CAMPAIGN_END,
    redeemed_window_start=CAMPAIGN_START,
    redeemed_window_end=CAMPAIGN_END,
    valid_tier_ids=(7, 15, 10022),
    background_mask="rgba(12, 4, 22, 0.22)",
    # QA earned TP; existing redemptions still reduce the available balance.
    balance_overrides={"OM000000001": 50000},
    test_profiles={"OM000000001": {"initials": "T.A.", "tier": "Test Account"}},
    logger_name="mickey",
)


dash.register_page(__name__, path=config.page_path, name="Mickey")
require_login(__name__, access_level=config.access_level)

page = ShoppingPage(__name__, config)
layout = page.layout
page.register_callbacks()
