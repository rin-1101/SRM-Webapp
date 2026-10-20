import sys
from pathlib import Path

import dash

PAGES_ROOT = Path(__file__).resolve().parent
if str(PAGES_ROOT) not in sys.path:
    sys.path.append(str(PAGES_ROOT))

ROOT = "\\\\ominfstdpsd10001p-fs.int.okadamanila.com\\Casino\\Strategic Marketing\\Database Admin\\ETL\\Applications\\okada"
sys.path.append(ROOT)

ROOT2 = "\\\\ominfstdpsd10001p-fs.int.okadamanila.com\\Casino\\Strategic Marketing\\Database Admin\\ETL\\Applications"
sys.path.append(f"{ROOT2}\\okada\\")
sys.path.append(f"{ROOT2}\\reports\\utils\\app_classes\\")

from utils.paths import BDEAG_VIEW
from utils.login_handler import require_login, restricted_page
from templates.shopping import ShopConfig, ShoppingPage

PATH_DB = r"\\ominfstdpsd10001p-fs.int.okadamanila.com\Casino\Strategic Marketing\Database Admin\ETL\Applications\reports\sqlite\inventory\bdeag.db"
PATH_DATA = r"\\ominfstdpsd10001p-fs.int.okadamanila.com\Casino\Strategic Marketing\Database Admin\ETL\Applications\reports\sqlite\shop"
PATH_INV = r"\\ominfstdpsd10001p-fs.int.okadamanila.com\Casino\Strategic Marketing\Database Admin\ETL\Applications\reports\sqlite\inventory"
PATH_TIER_CSV = r"\\ominfstdpsd10001p-fs.int.okadamanila.com\Casino\Strategic Marketing\Marketing Analysis\Campaigns\2607\BD Earn and Get\etl\history\tier-snap.csv"

CAMPAIGN_START = "2026-08-21 06:00:00"
CAMPAIGN_END = "2026-09-20 05:59:00"
REDEEMED_WINDOW_START = CAMPAIGN_START
REDEEMED_WINDOW_END = CAMPAIGN_END

BDCODING_TAGS = ("local", "korea", "sea", "japan")
BDCODING_INVENTORY_FILENAMES = {
    tag: f"bdeag-{tag}.db" for tag in BDCODING_TAGS
}

ENTITLEMENT_OVERRIDES = {
    "OM000000001": "local",
    "OM000000002": "sea",
    "OM000000003": "korea",
    "OM000000004": "japan",
}
UNLIMITED_REDEMPTION_UIDS = tuple(ENTITLEMENT_OVERRIDES)

config = ShopConfig(
    suffix="bdeag-view",
    page_path=BDEAG_VIEW,
    access_level=restricted_page[BDEAG_VIEW]["access_level"],

    path_db=PATH_DB,
    path_data=PATH_DATA,
    path_inv=PATH_INV,
    path_tier_csv=PATH_TIER_CSV,
    db_filename="bdeag.db",

    assets_folder="BDEAG",
    css_prefix="shop",
    logo="default",
    style_options=(
        "base",
        "minimalism",
        "liquid-glass",
        "velvet-noir",
        "champagne-gold",
        "neon-onyx",
        "silver",
        "bulma-default",
    ),
    default_style="silver",
    member_title=None,

    max_per_category=1,
    max_redemption=1,
    campaign_start=CAMPAIGN_START,
    campaign_end=CAMPAIGN_END,
    redeemed_window_start=REDEEMED_WINDOW_START,
    redeemed_window_end=REDEEMED_WINDOW_END,
    valid_tier_ids=(7, 15, 10022),
    allow_all_tiers=True,
    background_mask="rgba(20, 34, 52, 0.45)",
    quick_add=True,
    bdcoding=True,
    bdcoding_tags=BDCODING_TAGS,
    bdcoding_inventory_filenames=BDCODING_INVENTORY_FILENAMES,
    bdcoding_entitlement_overrides=ENTITLEMENT_OVERRIDES,
    unlimited_redemption_uids=UNLIMITED_REDEMPTION_UIDS,
    logger_name="bd-earn-and-get-view",
    view_only=True,
    low_power_mode=True,

    balance_overrides={
        uid: 5000000 for uid in ENTITLEMENT_OVERRIDES
    },
)

dash.register_page(__name__, path=config.page_path, name="BD Earn and Get View")
require_login(__name__, access_level=config.access_level)

page = ShoppingPage(__name__, config)
layout = page.layout
page.register_callbacks()
