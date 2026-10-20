import sys

import dash

from utils.paths import ENTITLEMENT
from utils.login_handler import require_login, restricted_page
from templates.entitlement import EntitlementConfig, EntitlementPage

ROOT = "\\\\ominfstdpsd10001p-fs.int.okadamanila.com\\Casino\\Strategic Marketing\\Database Admin\\ETL\\Applications"
sys.path.append(f"{ROOT}\\okada\\")
from okada import LogService

logger = LogService("entitlement-checker").get_logger()

WHITELIST_PATH = r"\\ominfstdpsd10001p-fs.int.okadamanila.com\Casino\Strategic Marketing\Marketing Analysis\Campaigns\2606\Weekday Appliances Rewards\Lists\Weekday Appliances Rewards Test Group.csv"

config = EntitlementConfig(
    suffix="weekday-appliances",
    page_path=ENTITLEMENT,
    access_level=restricted_page[ENTITLEMENT]["access_level"],
    whitelist_path=WHITELIST_PATH,
    default_map_columns=["UniversalPlayerID"],
    fetch_columns=["Prize"],
    title="Weekday Appliances Rewards Entitlement",
    logger=logger,
    dev=True
)

page = EntitlementPage(config)

dash.register_page(__name__, path=config.page_path)
require_login(__name__, access_level=config.access_level)
layout = page.layout
page.register_callbacks()