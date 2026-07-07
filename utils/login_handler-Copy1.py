import dash
from utils.paths import (
    TOP10_TG_WINNER_MASS_PATH,
    TOP10_TG_WINNER_ROLL_PATH,
    LOYALTYDB_REPORT_PATH,
    CASINOSLIPS_PATH,
    REDEMPTION_PATH,
    EGPLAYHOURS_PATH,
)


# Accounts and roles should be read from the DB

ACCOUNTS = {
    "kirstie.ylagan": {"role": "pne"},
    "kathrice.paredes": {"role": "pne"},
    "kamille.blanco": {"role": "pne"},
    "emmanuel.sy": {"role": "pne"},
    "dan.veniegas": {"role": "pne"},
    "christine.manatad": {"role": "pne"},
    "nino.concepcion": {"role": "pne"},
    "nezles.tantamco": {"role": "pne"},
    "jenny.sabado": {"role": "pne"},
    "carolyn.ugat": {"role": "pne"},
    "karen.naval": {"role": "pne"},
    "camille.medina": {"role": "pne"},
    "micah.jackson": {"role": "pne"},
    "joshua.bernabe": {"role": "pne"},
    "joe.sam": {"role": "loyalty"},
    "miyaki.varca": {"role": "loyalty"},
    "andrevictor.romero": {"role": "loyalty"},
    "marian.demonteverde": {"role": "loyalty"},
    "benjamin.cabalona": {"role": "admin"},
    "richie.chiu": {"role": "admin"},
    "nathaniel.cheok": {"role": "admin"},
    "aira.jimena": {"role": "sm"},
    "khazel.tenero": {"role": "sm"},
    "jenelyn.bantilan": {"role": "sm"},
    "jackiehilary.legaspi": {"role": "sm"},
    "wendy.ni": {"role": "smheads"},
}

restricted_page = {
    TOP10_TG_WINNER_MASS_PATH: {"access_level": ["admin", "smheads", "surveillance"]},
    TOP10_TG_WINNER_ROLL_PATH: {
        "access_level": ["admin", "user", "smheads", "surveillance"]
    },
    LOYALTYDB_REPORT_PATH: {"access_level": ["admin", "smheads", "loyalty-head"]},
    CASINOSLIPS_PATH: {"access_level": ["admin", "smheads"]},
    REDEMPTION_PATH: {"access_level": ["admin", "smheads", "loyalty", "pne"]},
    EGPLAYHOURS_PATH: {"access_level": ["admin", "smheads", "optimization"]},
}

pages_name = {
    TOP10_TG_WINNER_ROLL_PATH: "Top 10 TG Winner Rolling",
    TOP10_TG_WINNER_MASS_PATH: "Top 10 TG Winner Mass",
    LOYALTYDB_REPORT_PATH: "Loyalty Report",
    CASINOSLIPS_PATH: "Casino Slips",
    REDEMPTION_PATH: "Redemption Report",
    EGPLAYHOURS_PATH: "EG Play Hours",
}


def get_accessible_pages_by_role(role):
    accessible_pages = {}
    for page in restricted_page:
        if role in restricted_page[page]["access_level"]:
            accessible_pages[pages_name[page]] = page
    return accessible_pages


def require_login(page, **kwargs):
    for pg in dash.page_registry:
        if page == pg:
            restricted_page[dash.page_registry[pg]["path"]] = {}
            restricted_page[dash.page_registry[pg]["path"]]["restricted"] = True
            if "access_level" in kwargs:
                restricted_page[dash.page_registry[pg]["path"]][
                    "access_level"
                ] = kwargs["access_level"]


def has_access(user, path):
    return ACCOUNTS[user.id]["role"] in restricted_page[path]["access_level"]
