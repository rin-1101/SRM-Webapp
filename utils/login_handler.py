import dash
# from utils.paths import  LONG_ABSENT, EARN_YOUR_DRIVE, CRACK_THE_CODE, CRACK_THE_CODE_WEEKLY,  PAYDAY, DAILY_INSTANT, REDEMPTION_PATH, REDEMPTION_DAILY, CASINOSLIP, COPS_PATH, OVERCOMP, LOYALTYDB, NSU,WEEKLY_EARN_AND_GET, NA_WEEKLY_EARN_AND_GET,  LOCAL_TAILORED, FREEPLAY
from utils.paths import DYSON_LUXE_REWARDS,OOC_FUNZONE, RFR_CHECKER, RFR_RAFFLE, RFR_RAFFLE_GRAND,LOYALTYDB, DASHFORCASH, LEADERBOARD, REDEMPTION_PATH, REDEMPTION_DAILY, FIRE_HORSE_VIEW, PATRONDB, TRANSACTIONS, FIRE_HORSE,COMMS, CRACK_THE_CODE, CRACK_THE_CODE_WEEKLY, WED_RAFFLE, WED_RAFFLE_BACKEND, CASINOSLIP, FUWA, VIP_SHOP, TRANSACTIONS_VIEW, INVENTORY
from utils.get_users import get_users


# Accounts and roles should be read from the DB

ACCOUNTS = get_users()

restricted_page = {
    REDEMPTION_PATH: {
        "access_level": [
            "admin",
            "smheads",
            "sm",
            "loyalty",
            "pne",
            "bs",
            "bsheads",
            "dm",
            "ga",
            "ca",
            "pneset",
            "audit",
        ]
    },
    REDEMPTION_DAILY: {
        "access_level": [
            "admin",
            "smheads",
            "sm",
            "loyalty",
            "pne",
            "bs",
            "bsheads",
            "dm",
            "ga",
            "ca",
            "pneset",
            "audit"
        ]
    },
    CASINOSLIP: {"access_level": ["admin", "smheads", "sm", "ga", "ca", "bsheads"]},
    # NSU: {"access_level": ["admin", "smheads", "sm", "ga"]},
    # COPS_PATH: {"access_level": ["admin", "smheads", "sm", "cops", "bdheads"]},
    # OVERCOMP: {"access_level": ["admin", "overcomp", "sm", "bdheads", "bsheads","poheads","audit"]},
    LOYALTYDB: {"access_level": ["admin","smheads", "loyalty"]},
    # WEEKLY_EARN_AND_GET:{"access_level": ["admin","smheads","bdsea",'bdheads','cops',"maraffle","raffle"]},
    # NA_WEEKLY_EARN_AND_GET:{"access_level": ["admin","smheads","bdna",'bdheads','cops',"maraffle","raffle"]},
    # PAYDAY:{"access_level": ["admin", "smheads","maraffle","raffle","poheads", "pne","overcomp","cops","bdheads", "bdlocal", "bdheads", "bd"]},
    # DAILY_INSTANT:{"access_level": ["admin", "smheads"]},
    # LOCAL_TAILORED:{"access_level": ["admin","smheads","bdlocal",'bdheads','overcomp','cops',"maraffle","raffle"]},
    # FREEPLAY:{"access_level": ["admin", "smheads"]},
    VIP_SHOP:{"access_level": ["admin"]},
    CRACK_THE_CODE:{"access_level": ["admin"]},
    CRACK_THE_CODE_WEEKLY:{"access_level": ["admin"]},
    WED_RAFFLE: {"access_level": ["admin"]},
    WED_RAFFLE_BACKEND:{"access_level": ["admin", "smheads","raffle","maraffle","poheads", "pne","overcomp","cops","bdheads","bdlocal", "bdheads", "bd"]},
    COMMS:{"access_level": ["admin", "smheads"]},
    INVENTORY:{"access_level": ["admin", "smheads","maraffle","raffle","poheads", "pne","overcomp","cops","bdheads"]},
    FUWA:{"access_level": ["admin"]},
    FIRE_HORSE:{"access_level": ["admin", "smheads","maraffle","raffle","poheads", "pne","overcomp","cops","bdheads", "bdlocal", "bdheads", "bd"]},
    FIRE_HORSE_VIEW:{"access_level": ["admin", "smheads","maraffle","raffle","poheads", "pne","overcomp","cops","bdheads", "bdlocal", "bdheads", "bd"]},
    TRANSACTIONS:{"access_level": ["admin", "smheads","maraffle","poheads", "pne","overcomp","cops","bdheads"]},
    TRANSACTIONS_VIEW:{"access_level": ["admin", "smheads","maraffle","raffle","poheads", "pne","overcomp","cops","bdheads"]},
    PATRONDB:{"access_level": ["admin", "smheads","bdheads","bd","cops","maraffle","poheads"]},
    LEADERBOARD:{"access_level": ["admin"]},
    DASHFORCASH:{"access_level": ["admin", "smheads","raffle","maraffle","poheads", "pne","overcomp","cops","bdheads","bdlocal", "bdheads", "bd"]},
    RFR_RAFFLE:{"access_level": ["admin", "smheads","raffle","maraffle","poheads", "pne","overcomp","cops","bdheads","bdlocal", "bdheads", "bd"]},
    RFR_RAFFLE_GRAND:{"access_level": ["admin", "smheads","raffle","maraffle","poheads", "pne","overcomp","cops","bdheads","bdlocal", "bdheads", "bd"]},
    RFR_CHECKER:{"access_level": ["admin", "smheads","raffle","maraffle","poheads", "pne","overcomp","cops","bdheads","bdlocal", "bdheads", "bd"]},
    OOC_FUNZONE:{"access_level": ["admin", "smheads","raffle","maraffle","poheads", "pne","overcomp","cops","bdheads","bdlocal", "bdheads", "bd"]},
    DYSON_LUXE_REWARDS:{"access_level": ["admin"]},
    # EARN_YOUR_DRIVE:{"access_level": ["admin", "smheads","maraffle","raffle","poheads", "pne","overcomp","cops","bdheads", "bdlocal", "bdheads", "bd"]},
    # LONG_ABSENT:{"access_level": ["admin", "smheads","maraffle","raffle","poheads", "pne","overcomp","cops","bdheads", "bdlocal", "bdheads", "bd"]},

}

pages_name = {
    REDEMPTION_PATH: "Redemption Report",
    REDEMPTION_DAILY: "Redemption Daily",
    CASINOSLIP: "Casino Slip",
    # COPS_PATH: "COPS",
    # OVERCOMP: "Overcomp",
    LOYALTYDB: "Loyalty Report",
    # NSU: "MASS NSU",
    # WEEKLY_EARN_AND_GET:"SEA Monthly Earn and Get",
    # NA_WEEKLY_EARN_AND_GET:"NA Monthly Earn and Get",
    # LOCAL_TAILORED: 'BD LOCAL- TAILORED PROGRAM',
    # LONG_ABSENT:"Long Absent tracker",
    # PAYDAY:'PayDay Tracking',
    # DAILY_INSTANT:'Daily Instant Tracking',
    # FREEPLAY : 'Free Play Tracking',
    CRACK_THE_CODE : 'Crack The Code',
    CRACK_THE_CODE_WEEKLY : 'Crack The Code Weekly Draw',
    WED_RAFFLE : 'Win it Wednesday',
    WED_RAFFLE_BACKEND : 'Raffle Backend',
    COMMS : 'Communications',
    FUWA : 'Master Fuwa Raffle',
    VIP_SHOP : 'VIP Shopping Galore',
    TRANSACTIONS_VIEW : 'Transactions View',
    TRANSACTIONS : 'Transactions',
    INVENTORY : 'Inventory',
    FIRE_HORSE : 'Bespoke Fire Horse Collection',
    FIRE_HORSE_VIEW : 'Bespoke Fire Horse Collection View',
    PATRONDB : 'Patron Database',
    LEADERBOARD : 'Leaderboards',
    DASHFORCASH : 'Dash For Cash',
    RFR_RAFFLE : 'Reels for Relaxation for all',
    RFR_RAFFLE_GRAND : 'Reels for Relaxation Grand Draw',
    RFR_CHECKER : 'Reels for Relaxation Checker',
    OOC_FUNZONE : "OOC Funzone",    
    DYSON_LUXE_REWARDS : "Dyson Luxe Rewards",
    # EARN_YOUR_DRIVE:'Bet on Your Drive',
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
