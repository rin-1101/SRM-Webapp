import dash
from dash import dcc, html, Input, Output, State, callback
import sys
import math
import re
import sqlite3
import pandas as pd
from datetime import datetime, date, timedelta

from utils.login_handler import require_login, has_access, restricted_page
from utils.paths import FIRE_HORSE_VIEW  # ← add this path to your paths.py

# ============================================================
#  Path / App Setup
# ============================================================
ROOT = "\\\\ominfstdpsd10001p-fs.int.okadamanila.com\\Casino\\Strategic Marketing\\Database Admin\\ETL\\Applications\\okada"
sys.path.append(ROOT)
from okada import SQL, SQLService
from okada.utils.format import comma_format, human_format
from okada import LogService

ROOT2 = "\\\\ominfstdpsd10001p-fs.int.okadamanila.com\\Casino\\Strategic Marketing\\Database Admin\\ETL\\Applications"
sys.path.append(f"{ROOT2}\\okada\\")
sys.path.append(f"{ROOT2}\\reports\\utils\\app_classes\\")

from shop import ShopTransaction

dash.register_page(__name__, path=FIRE_HORSE_VIEW)
require_login(__name__, access_level=restricted_page[FIRE_HORSE_VIEW]["access_level"])

logger = LogService("fire-horse-view").get_logger()

# ============================================================
#  File Paths
# ============================================================
PATH_DB       = r"\\ominfstdpsd10001p-fs.int.okadamanila.com\Casino\Strategic Marketing\Database Admin\ETL\Applications\reports\sqlite\inventory\afhc.db"
PATH_DATA     = r"\\ominfstdpsd10001p-fs.int.okadamanila.com\Casino\Strategic Marketing\Database Admin\ETL\Applications\reports\sqlite\shop"
PATH_TIER_CSV = r"\\ominfstdpsd10001p-fs.int.okadamanila.com\Casino\Strategic Marketing\Marketing Analysis\Campaigns\2507\VIP Shopping Galore\etl\history\tier-snap.csv"

CAMPAIGN_START   = "2026-05-11 06:00:00"
CAMPAIGN_END     = "2026-06-07 05:59:00"

# ============================================================
#  Helpers
# ============================================================

def get_loader():
    return SQL("halo").get_loader()


def format_om(om: int | str) -> str:
    return f"OM{str(om).zfill(9)}"


def get_tier(uid: str) -> str:
    hist = pd.read_csv(PATH_TIER_CSV)
    hist["UniversalPlayerID"] = hist["UniversalPlayerID"].astype(str).str.strip()
    filtered = hist[hist["UniversalPlayerID"] == uid.strip()]
    if not filtered.empty:
        return filtered.iloc[0]["Tier"]

    sql = f"""
        SELECT UniversalPlayerID,
            CASE
                WHEN TierID = 7     THEN 'Supreme'
                WHEN TierID = 15    THEN 'Maharlika'
                WHEN TierID = 10022 THEN 'Maharlika'
                ELSE 'NA'
            END AS TierName
        FROM ENGAGEDB.dbo.UC_PL_Player p
        LEFT JOIN ENGAGEDB.dbo.UC_PL_Tier t ON t.PlayerID = p.PlayerID
        WHERE UniversalPlayerID = '{uid}'
          AND t.TierID IN (7, 15, 10022)
    """
    result = get_loader().load_data(sql)
    return result.iloc[0]["TierName"] if not result.empty else "NA"


def get_balance(uid: str) -> int:
    if uid == "OM000000001":
        return 50000

    sql = f"""
        SELECT p.UniversalPlayerID AS uid, tp.PlayerID, SUM(tp.TierPoint) AS Sum_TP
        FROM [ENGAGEDB].[dbo].[UC_PL_Rating] r
        LEFT JOIN [ENGAGEDB].[dbo].[UC_PL_Player] p          ON r.PlayerID   = p.PlayerID
        LEFT JOIN [ENGAGEDB].[dbo].[UC_PL_TierPointDetailActual] tp ON r.RatingID = tp.RatingID
        WHERE r.TransactionDateTime >= '{CAMPAIGN_START}'
          AND r.TransactionDateTime  < '{CAMPAIGN_END}'
          AND p.UniversalPlayerID = '{uid}'
        GROUP BY p.UniversalPlayerID, tp.PlayerID
        ORDER BY p.UniversalPlayerID, tp.PlayerID
    """
    tp_earn = get_loader().load_data(sql)
    if tp_earn.empty:
        return 0
    tp_earn = tp_earn[tp_earn["Sum_TP"] > 0]
    tp_earn["uid"] = tp_earn["uid"].str.strip()
    return math.ceil(tp_earn["Sum_TP"].sum())


def get_redeemed(uid: str) -> int:
    shop = ShopTransaction(PATH_DATA, "afhc.db", "orders", user="redeem-app")
    return int(shop.get_total_redeemed(uid) or 0)


def find_initials(om_number: str) -> str:
    sql = f"""
        SELECT [FirstName] AS fn, [LastName] AS ln
        FROM [ENGAGEDB].[dbo].[UC_PL_Player]
        WHERE UniversalPlayerID = '{om_number}'
    """
    result = get_loader().load_data(sql)
    return f"{result.loc[0, 'fn'][0]}.{result.loc[0, 'ln'][0]}."


def read_prize_pool() -> pd.DataFrame:
    conn = sqlite3.connect(PATH_DB)
    df = pd.read_sql_query("SELECT * FROM prize_pool ORDER BY cost ASC", conn)
    conn.close()
    return df


# ============================================================
#  Layout
# ============================================================

def layout():
    return html.Div(
        style={"width": "100vw", "height": "100vh"},
        id="main-container-view",
        children=[
            html.Link(rel="stylesheet", href="/assets/afhc/style.css"),

            # Logo
            html.Div(
                style={"text-align": "center"},
                children=[
                    html.Img(
                        id="logo-main-view",
                        src="/assets/afhc/logo.png",
                        style={
                            "height": "300px", "width": "auto", "max-width": "100%",
                            "object-fit": "contain", "marginBottom": "-30vh", "marginTop": "5vh"
                        }
                    )
                ]
            ),

            # Player search section
            html.Section(
                className="section is-vcentered is-centered is-flex is-fullheight",
                children=[
                    html.Div(
                        id="main-container-items-view",
                        className="columns is-vcentered is-centered is-flex is-fullheight",
                        style={"paddingTop": "30vh"},
                        children=[
                            # Logo column
                            html.Div(
                                className="column is-one-quarter has-text-centered",
                                children=[html.Img(src="/assets/DEFAULT/logo-cream.png")]
                            ),
                            # Input column
                            html.Div(
                                className="column",
                                style={"marginRight": "5rem"},
                                children=[
                                    # OM number + Check button
                                    html.Div(className="columns is-gapless", children=[
                                        html.Div(className="column is-two-thirds", children=[
                                            html.Div(className="search-box box-afhc", children=[
                                                dcc.Input(
                                                    id="uid-textbox-view",
                                                    type="number",
                                                    placeholder="Enter OM Number",
                                                    className="search-input input is-medium has-text-centered",
                                                    autoComplete="off",
                                                    style={"width": "100%"}
                                                )
                                            ])
                                        ]),
                                        html.Div(
                                            className="column is-one-third",
                                            style={"display": "flex", "justifyContent": "center", "alignItems": "center"},
                                            children=[
                                                html.Button(
                                                    "Check",
                                                    id="check-button-view",
                                                    n_clicks=0,
                                                    className="button-afhc button",
                                                    style={"width": "100%"}
                                                )
                                            ]
                                        ),
                                    ]),
                                    # Initials + Tier row
                                    html.Div(className="columns is-centered", children=[
                                        html.Div(className="column is-one-third", children=[
                                            html.Div(className="search-box box-afhc", children=[
                                                dcc.Input(
                                                    id="initials-textbox-view",
                                                    type="text",
                                                    placeholder="Initials",
                                                    className="search-input input is-medium has-text-centered",
                                                    disabled=True
                                                )
                                            ])
                                        ]),
                                        html.Div(className="column is-two-thirds", children=[
                                            html.Div(className="search-box box-afhc", children=[
                                                dcc.Input(
                                                    id="tier-textbox-view",
                                                    type="text",
                                                    placeholder="Tier",
                                                    className="search-input input is-medium has-text-centered",
                                                    disabled=True
                                                )
                                            ])
                                        ]),
                                    ]),
                                ]
                            ),
                        ]
                    )
                ]
            ),

            # Error text
            html.Div(id="error-text-view", className="has-text-danger has-text-centered"),

            # TP Credits section (hidden until Check)
            html.Div(
                id="credits-section-view",
                style={"display": "none"},
                children=[
                    html.Div(
                        className="columns is-centered is-vcentered is-mobile",
                        children=[
                            html.Div(className="column is-3", children=[
                                html.Section(className="section has-text-centered", children=[
                                    html.H2("TP Earned", className="title is-4"),
                                    html.Div(
                                        className="is-flex is-justify-content-center search-box box-afhc",
                                        children=[
                                            dcc.Input(
                                                id="tp-display-view",
                                                type="text",
                                                placeholder="0",
                                                className="input is-medium has-text-centered search-input",
                                                disabled=True
                                            )
                                        ]
                                    )
                                ])
                            ]),
                            html.Div(className="column is-3", children=[
                                html.Section(className="section has-text-centered", children=[
                                    html.H2("TP Redeemed", className="title is-4"),
                                    html.Div(
                                        className="is-flex is-justify-content-center search-box box-afhc",
                                        children=[
                                            dcc.Input(
                                                id="tp-redeem-view",
                                                type="text",
                                                placeholder="0",
                                                className="input is-medium has-text-centered search-input",
                                                disabled=True
                                            )
                                        ]
                                    )
                                ])
                            ]),
                            html.Div(className="column is-4", children=[
                                html.Section(className="section has-text-centered", children=[
                                    html.H2("TP Balance", className="title is-4"),
                                    html.Div(
                                        className="is-flex is-justify-content-center search-box box-afhc",
                                        children=[
                                            dcc.Input(
                                                id="tp-balance-view",
                                                type="text",
                                                placeholder="0",
                                                className="input is-medium has-text-centered search-input",
                                                disabled=True
                                            )
                                        ]
                                    )
                                ])
                            ]),
                        ]
                    )
                ]
            ),

            # Items grid (view-only, no qty controls)
            html.Section(
                className="section",
                children=[
                    html.Div(
                        id="items-grid-view",
                        className="columns is-multiline is-mobile is-centered",
                        style={"maxWidth": "100vw", "margin": "0 auto"},
                        children=[]
                    )
                ]
            ),
        ]
    )


# ============================================================
#  Callback — Check button
# ============================================================

@callback(
    Output("initials-textbox-view",      "value"),
    Output("tier-textbox-view",          "value"),
    Output("tp-display-view",            "value"),
    Output("tp-redeem-view",             "value"),
    Output("tp-balance-view",            "value"),
    Output("credits-section-view",       "style"),
    Output("main-container-items-view",  "style"),
    Output("error-text-view",            "children"),
    Output("items-grid-view",            "children"),
    Output("logo-main-view",             "style"),
    Input("check-button-view",           "n_clicks"),
    State("uid-textbox-view",            "value"),
    prevent_initial_call=True,
)
def on_check(n_clicks, om_number):
    HIDDEN   = {"display": "none"}
    LOGO_VISIBLE = {
        "height": "300px", "width": "auto", "max-width": "100%",
        "object-fit": "contain", "marginBottom": "-30vh", "marginTop": "5vh"
    }
    NO_ITEMS = []

    def _reject(msg, initials="", tier=""):
        return initials, tier, "", "", "", HIDDEN, {"paddingTop": "30vh"}, msg, NO_ITEMS, LOGO_VISIBLE

    if not om_number:
        return _reject("❌ Please enter a valid OM Number.")

    om = format_om(om_number)

    try:
        initials = find_initials(om)
    except Exception:
        initials = "Not found"

    tier = get_tier(om)
    if tier == "NA":
        return _reject("❌ Patron is not qualified.", initials=initials, tier=tier)

    balance = get_balance(om)
    if balance < 1:
        return _reject("❌ No earning for this OM.", initials=initials, tier=tier)

    redeemed   = get_redeemed(om)
    tp_balance = max(0, balance - redeemed)

    # Build view-only item grid — only show affordable, in-stock items
    df         = read_prize_pool()
    item_cards = []
    for i in df.index:
        row        = df.loc[i]
        affordable = row["cost"] <= tp_balance
        in_stock   = row["inventory"] > 0

        if not affordable or not in_stock:
            continue

        item_cards.append(
            html.Div(
                className="column is-half",
                children=[
                    html.Div(
                        className="card afhc-card",
                        children=[
                            html.Div(
                                className="card-image",
                                children=[
                                    html.Img(
                                        src=f"/assets/inventory/afhc/{row['ID']}.png",
                                        className="image-card-afhc"
                                    )
                                ]
                            ),
                            html.Div(
                                className="card-content has-text-centered afhc-card-content",
                                children=[
                                    html.P(row["name"],         className="title is-6 afhc-card-title"),
                                    html.P(f"{row['cost']} TP", className="subtitle is-7 afhc-card-subtitle"),
                                ]
                            ),
                        ]
                    )
                ]
            )
        )

    logger.info(f"View check: {om} | TP earned={balance} redeemed={redeemed} balance={tp_balance}")

    return (
        initials,
        tier,
        str(balance),
        str(redeemed),
        str(tp_balance),
        {"display": "block"},
        {"transition": "all 0.3s ease-in-out", "paddingTop": "0vh"},
        "",
        item_cards,
        HIDDEN,
    )
