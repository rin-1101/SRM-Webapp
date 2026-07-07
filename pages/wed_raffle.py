"""
pages/wed_raffle.py
===================
Win-It-Wednesday raffle page.
"""

import sys
import dash

from utils.paths import WED_RAFFLE
from utils.login_handler import require_login, restricted_page

ROOT = "\\\\ominfstdpsd10001p-fs.int.okadamanila.com\\Casino\\Strategic Marketing\\Database Admin\\ETL\\Applications"
sys.path.append(f"{ROOT}\\okada\\")
sys.path.append(f"{ROOT}\\reports\\pages\\")
# sys.path.append(f"{ROOT}\\reports\\templates\\")

from raffle_etl.raffle import Raffle_app
from raffle_etl.shareddata import get_data
from templates.raffle import RafflePage
from okada import LogServiceDaily

logger = LogServiceDaily("win-wed").get_logger()

raffle = Raffle_app()

dash.register_page(__name__, path=WED_RAFFLE)
require_login(__name__, access_level=restricted_page[WED_RAFFLE]["access_level"])
##

class WedRaffle(RafflePage):
    page_path    = WED_RAFFLE
    access_level = restricted_page[WED_RAFFLE]["access_level"]

    store_key    = "win_it_wednesday"
    container_id = "container-div-wed"

    bg_image      = "/assets/raffle/wed-raffle/Background/BG 1.jpg"
    logo_src      = "/assets/raffle/wed-raffle-logo.png"
    logo_height   = "300px"
    date_img_dir  = "/assets/raffle/wed-raffle/Dates"
    time_img_dir  = "/assets/raffle/wed-raffle/Time"
    prize_img_dir = "/assets/raffle/wed-raffle/Prizes"
    php_img       = "PHP.png"
    worth_img     = "WORTH.png"

    font_class       = "raffle-font"
    default_uid_text = "Draw is about to Begin"
    standby_text     = "Next Draw at 10PM"

    poll_interval_ms   = 1_000
    anim_interval_ms   = 100
    animation_window_s = 3.0
    trigger_window_s   = 5.0


_page = WedRaffle(raffle, get_data_fn=get_data)

layout = _page.layout

_page._register_callbacks()