import dash
import sys
import pandas as pd

from dash import dcc, html, Input, Output, State, callback

from utils.login_handler import require_login, has_access, restricted_page
from utils.paths import RFR_CHECKER

from datetime import datetime, timedelta
# ============================================================
#  Path / App Setup
# ============================================================
ROOT = "\\\\ominfstdpsd10001p-fs.int.okadamanila.com\\Casino\\Strategic Marketing\\Database Admin\\ETL\\Applications\\okada"
sys.path.append(ROOT)
from okada import SQL, SQLService
from okada.utils.format import comma_format, human_format
from okada import LogService

dash.register_page(__name__, path=RFR_CHECKER)
require_login(__name__, access_level=restricted_page[RFR_CHECKER]["access_level"])

logger = LogService("reels-for-fortune-view").get_logger()

WHITELIST_PATH = r"\\ominfstdpsd10001p-fs.int.okadamanila.com\Casino\Strategic Marketing\Database Admin\ETL\Applications\reports\documents\reels_for_relaxation.csv"

# ============================================================
#  Helpers
# ============================================================

def get_loader():
    return SQL("halo").get_loader()


def format_om(om: int | str) -> str:
    return f"OM{str(om).zfill(9)}"
def _img(src: str, height: str = "auto", extra_style: dict = None):
    style = {
        "height": height,
        "width": "auto",
        "maxWidth": "100%",
        "objectFit": "contain",
    }
    if extra_style:
        style.update(extra_style)
    return html.Img(src=src, style=style)

def get_entries(om_number: str) -> int:
    """Return the number of entries the patron has. Returns 0 if not in whitelist."""
    if om_number == "OM000000001":
        return 99

    whitelist_df = pd.read_csv(WHITELIST_PATH)
    whitelist_df["UniversalPlayerID"] = whitelist_df["UniversalPlayerID"].astype(str).str.strip()

    row = whitelist_df[whitelist_df["UniversalPlayerID"] == om_number.strip()]
    if row.empty:
        return 0

    return int(row.iloc[0]["Entries"])


def find_initials(om_number: str) -> str:
    sql = f"""
        SELECT [FirstName] AS fn, [LastName] AS ln
        FROM [ENGAGEDB].[dbo].[UC_PL_Player]
        WHERE UniversalPlayerID = '{om_number}'
    """
    result = get_loader().load_data(sql)
    return f"{result.loc[0, 'fn'][0]}.{result.loc[0, 'ln'][0]}."


# ============================================================
#  Layout
# ============================================================

def layout():
    return html.Div(
        id="main-container-rfr",
        style={
            "width": "100vw",
            "height": "100vh",
            "display": "flex",
            "flexDirection": "column",
            "alignItems": "center",
            "justifyContent": "center",
        },
        children=[
            html.Link(rel="stylesheet", href="/assets/rfr/style.css"),

            # ── Search card ──────────────────────────────────
            html.Div(
                className="rfr-card",
                children=[
                    # OM input + Check button
                    html.Div(className="columns is-gapless is-mobile", children=[
                        html.Div(className="column om-column", children=[
                            html.Div(className="box-rfr", children=[
                                dcc.Input(
                                    id="uid-textbox-rfr",
                                    type="text",
                                    inputMode="numeric",
                                    placeholder="Enter OM Number",
                                    className="search-input input is-medium has-text-centered",
                                    autoComplete="off",
                                )
                            ])
                        ]),
                        html.Div(className="column button-column", children=[
                            html.Button(
                                "Check",
                                id="check-button-rfr",
                                n_clicks=0,
                                className="button-rfr button",
                            )
                        ]),
                    ]),

                    # Initials row
                    html.Div(className="columns", children=[
                        html.Div(className="column", children=[
                            html.Div(className="box-rfr", children=[
                                dcc.Input(
                                    id="initials-textbox-rfr",
                                    type="text",
                                    placeholder="Initials",
                                    className="search-input input is-medium has-text-centered",
                                    disabled=True
                                )
                            ])
                        ]),
                    ]),

                    # Error text
                    html.Div(
                        id="error-text-rfr",
                        className="has-text-danger has-text-centered"
                    ),

                    # Entries only (hidden until Check)
                    html.Div(
                        id="qualification-section-rfr",
                        style={"display": "none"},
                        children=[
                            html.Section(
                                className="section has-text-centered",
                                children=[
                                    html.H2("Entries", className="title is-4"),
                                    html.Div(
                                        className="box-rfr",
                                        children=[
                                            dcc.Input(
                                                id="entries-display-rfr",
                                                type="text",
                                                placeholder="0",
                                                className="search-input input is-medium has-text-centered",
                                                disabled=True
                                            )
                                        ]
                                    )
                                ]
                            )
                        ]
                    ),
                    # Entries only (hidden until Check)
                    
                    html.Div(
                        id="message-section-rfr",
                        children=[html.Img(src=f"/assets/rfr/body.png")]
                    ),
                ]
            ),

            # kept hidden in DOM so callback output stays valid
            dcc.Input(id="tier-textbox-rfr",           type="text", style={"display": "none"}),
            dcc.Input(id="qualification-status-rfr",   type="text", style={"display": "none"}),
        ]
    )


# ============================================================
#  Callback — Check button
# ============================================================

@callback(
    Output("initials-textbox-rfr",       "value"),
    Output("tier-textbox-rfr",           "value"),
    Output("entries-display-rfr",        "value"),
    Output("qualification-status-rfr",   "value"),
    Output("qualification-section-rfr",  "style"),
    Output("error-text-rfr",             "children"),
    Input("check-button-rfr",            "n_clicks"),
    State("uid-textbox-rfr",             "value"),
    prevent_initial_call=True,
)
def on_check(n_clicks, om_number):
    HIDDEN = {"display": "none"}

    def _reject(msg, initials=""):
        return initials, "", "", "", HIDDEN, msg

    if not om_number:
        return _reject("Please enter a valid OM Number.")

    om = format_om(om_number)

    try:
        initials = find_initials(om)
    except Exception:
        initials = "Not found"

    entries   = get_entries(om)
    qualified = entries > 0
    status    = "QUALIFIED" if qualified else "NOT QUALIFIED"

    logger.info(f"Reels for Fortune check: {om} | entries={entries} | qualified={qualified}")

    return (
        initials,
        "",
        str(entries),
        status,
        {"display": "block"},
        "",
    )