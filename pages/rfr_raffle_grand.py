"""
pages/wed_raffle.py
===================
reels for relaxation raffle page.
"""

import sys
import dash

from utils.paths import RFR_RAFFLE_GRAND
from utils.login_handler import require_login, restricted_page

ROOT = "\\\\ominfstdpsd10001p-fs.int.okadamanila.com\\Casino\\Strategic Marketing\\Database Admin\\ETL\\Applications"
sys.path.append(f"{ROOT}\\okada\\")
sys.path.append(f"{ROOT}\\reports\\pages\\")
# sys.path.append(f"{ROOT}\\reports\\templates\\")

from raffle_etl.raffle import Raffle_app
from raffle_etl.shareddata import get_data
from templates.raffle import RafflePage
from okada import LogServiceDaily

raffle_key = RFR_RAFFLE_GRAND

logger = LogServiceDaily("win-wed").get_logger()

raffle = Raffle_app()

dash.register_page(__name__, path=raffle_key)
require_login(__name__, access_level=restricted_page[raffle_key]["access_level"])
##

class RfrRaffle(RafflePage):
    page_path    = raffle_key
    access_level = restricted_page[raffle_key]["access_level"]

    store_key    = "reels_for_relaxation_grand"
    container_id = "container-div-rfrg"

    bg_image      = "/assets/raffle/rfr-raffle/Background/BG.png"
    logo_src      = "/assets/raffle/rfr-raffle/logo.png"
    logo_height   = "750px"
    date_img_dir  = "/assets/raffle/rfr-raffle/Dates"
    time_img_dir  = "/assets/raffle/rfr-raffle/Time"
    prize_img_dir = "/assets/raffle/rfr-raffle/Prizes"
    php_img       = "PHP.png"
    worth_img     = "WORTH.png"

    font_class       = "raffle-font"
    default_uid_text = "Draw is about to Begin"
    standby_text     = "Next Draw at 10PM"

    poll_interval_ms   = 1_000
    anim_interval_ms   = 100
    animation_window_s = 3.0
    trigger_window_s   = 5.0


_page = RfrRaffle(raffle, get_data_fn=get_data, show_prize=True, show_time=False)

layout = _page.layout

_page._register_callbacks()