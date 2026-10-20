import sys
from pathlib import Path

import dash

PAGES_ROOT = Path(__file__).resolve().parent
if str(PAGES_ROOT) not in sys.path:
    sys.path.append(str(PAGES_ROOT))

ROOT = r"\\ominfstdpsd10001p-fs.int.okadamanila.com\Casino\Strategic Marketing\Database Admin\ETL\Applications"
sys.path.append(f"{ROOT}\\okada\\")
sys.path.append(f"{ROOT}\\reports\\pages\\")

from templates.raffle import RaffleApp, RafflePage
from utils.login_handler import require_login, restricted_page
from utils.paths import SNOWBALL_MANIA


class SnowballManiaPage(RafflePage):
    page_path = SNOWBALL_MANIA
    access_level = restricted_page[SNOWBALL_MANIA]["access_level"]
    store_key = "snowball_mania"
    container_id = "container-div-snowball-mania"

    bg_image = "/assets/snowball/bg2.png"
    logo_src = "/assets/snowball/logo2.png"
    logo_height = "260px"
    font_class = "raffle-font snowball-font"
    date_img_dir = "/assets/snowball/Dates"
    time_img_dir = "/assets/snowball/Time"
    prize_img_dir = "/assets/snowball/Prizes"

    default_uid_text = "Raffle is about to Begin"
    standby_text = "Next Raffle Draw Soon"


raffle = RaffleApp()
page = SnowballManiaPage(raffle)

dash.register_page(__name__, path=page.page_path, name="Snowball Mania")
require_login(__name__, access_level=page.access_level)

layout = page.layout
page._register_callbacks()