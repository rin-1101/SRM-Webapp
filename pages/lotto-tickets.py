import sys
from pathlib import Path

import dash

PAGES_ROOT = Path(__file__).resolve().parent
if str(PAGES_ROOT) not in sys.path:
    sys.path.append(str(PAGES_ROOT))

from templates.lotto import LottoTicketsPage
from utils.login_handler import require_login, restricted_page
from utils.paths import LOTTO_TICKETS


dash.register_page(__name__, path=LOTTO_TICKETS, name="Lotto Tickets")
require_login(__name__, access_level=restricted_page[LOTTO_TICKETS]["access_level"])

page = LottoTicketsPage()
layout = page.layout
page.register_callbacks()
