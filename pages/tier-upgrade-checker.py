import logging
import re
import sys
from datetime import date
from pathlib import Path

import dash
import pandas as pd
from dash import Input, Output, State, callback, dash_table, dcc, html
from flask_login import current_user

from utils.login_handler import has_access, require_login, restricted_page
from utils.paths import TIER_UPGRADE_CHECKER


ROOT = "\\\\ominfstdpsd10001p-fs.int.okadamanila.com\\Casino\\Strategic Marketing\\Database Admin\\ETL\\Applications\\okada"
sys.path.append(ROOT)

from okada import SQL


"""
RULES:

Patrons can only get a tier upgrade gift once in their lifetime per Tier.
So a Patron can get a Supreme Gift and a Maharlika Gift, but not two Supreme Gifts.

Tier point Balance must be at least 15,000 to be eligible for a tier upgrade gift for Maharlika and 2,500 for Supreme.

First we Check Tier

Supreme TierID = 7
Maharlika TierID = 15


you can check if a patron has already received a tier upgrade gift by checking the prize_red table for any rows with the patron's UID and an event name that contains "upgrade" and "gift".

"""
logger = logging.getLogger("tier-upgrade-checker")
UID_PATTERN = re.compile(r"^[A-Za-z0-9]+$")
TIER_RULES = {
    "Supreme": {"tier_id": 7, "point_threshold": 2_500},
    "Maharlika": {"tier_id": 15, "point_threshold": 15_000},
}
DEFAULT_TIER = "Maharlika"
TIER_HISTORY_COLUMNS = ["UniversalPlayerID", "FromTier", "ToTier", "CreatedDate"]
PRIZE_RED_COLUMNS = [
    "UniversalPlayerID",
    "EventName",
    "RedemptionGamingDate",
    "Value",
]
TIER_RESULT_COLUMNS = ["UniversalPlayerID", "gamingdate", "tierpoints"]


dash.register_page(
    __name__,
    path=TIER_UPGRADE_CHECKER,
    name="Tier Upgrade Checker",
)
require_login(
    __name__,
    access_level=restricted_page[TIER_UPGRADE_CHECKER]["access_level"],
)


def normalize_uid(value):
    uid = str(value or "").strip().upper()
    if not uid:
        raise ValueError("Please enter a UID.")
    if not UID_PATTERN.fullmatch(uid):
        raise ValueError("UID may contain letters and numbers only.")
    return uid


def normalize_start_year(value):
    if value is None or value == "":
        raise ValueError("Please select a gaming start year.")
    if not re.fullmatch(r"[0-9]{4}", str(value)):
        raise ValueError("Please select a valid gaming start year.")
    year = int(value)
    if not 1900 <= year <= date.today().year:
        raise ValueError("Please select a valid gaming start year.")
    return year


def normalize_tier(value):
    if not isinstance(value, str) or value not in TIER_RULES:
        raise ValueError("Please select Supreme or Maharlika.")
    return value


def build_queries(uid, start_year, tier=DEFAULT_TIER):
    uid = normalize_uid(uid)
    tier_rule = TIER_RULES[normalize_tier(tier)]
    start_date = date(normalize_start_year(start_year), 1, 1).isoformat()
    tier_history_query = f"""
SELECT player.UniversalPlayerID,
       from_tier.TierName AS FromTier,
       to_tier.TierName AS ToTier,
       history.CreatedDate
FROM ENGAGEDB.dbo.UC_PL_TierHist AS history
LEFT JOIN ENGAGEDB.dbo.UC_X_Tier AS from_tier
    ON history.FromTierID = from_tier.TierID
LEFT JOIN ENGAGEDB.dbo.UC_X_Tier AS to_tier
    ON history.ToTierID = to_tier.TierID
LEFT JOIN ENGAGEDB.dbo.UC_PL_Player AS player
    ON player.PlayerID = history.PlayerID
WHERE history.ToTierID = {tier_rule['tier_id']}
  AND history.ToTierID != history.FromTierID
  AND player.UniversalPlayerID = '{uid}'
ORDER BY history.CreatedDate DESC
"""
    prize_red_query = f"""
WITH subq AS (
    SELECT pr.PlayerID,
           event.Name AS EventName,
           event.Description AS EventDescription,
           prize.Name AS PrizeName,
           prize.Description AS PrizeDescription,
           prize.Value,
           pr.RedemptionDate,
           detail.PrizeRedemptionID AS VoucherNumber,
           CAST(CONVERT(
               varchar(10),
               IIF(
                   DATEPART(hour, pr.RedemptionDate) < 6,
                   DATEADD(day, -1, pr.RedemptionDate),
                   pr.RedemptionDate
               ),
               101
           ) AS date) AS RedemptionGamingDate,
           UPPER(pr.RedeemedBy) AS RedeemedBy,
           detail.Returned,
           detail.ReturnedDate,
           detail.ReturnedBy
    FROM ENGAGEDB.AWA.UC_PL_PrizeRedemption AS pr
    LEFT JOIN ENGAGEDB.AWA.UC_X_EventDefinition AS event
        ON pr.EventDefinitionID = event.ID
    LEFT JOIN ENGAGEDB.AWA.UC_PL_PrizeRedemptionDetail AS detail
        ON pr.ID = detail.PrizeRedemptionID
    LEFT JOIN ENGAGEDB.AWA.UC_X_PrizeInventory AS prize
        ON detail.PrizeID = prize.ID
    LEFT JOIN ENGAGEDB.dbo.UC_X_Bucket AS bucket
        ON prize.RequiredBucketTypeID = bucket.BucketID
)
SELECT player.UniversalPlayerID,
       subq.EventName,
       subq.RedemptionGamingDate,
       subq.Value
FROM subq
LEFT JOIN ENGAGEDB.dbo.UC_PL_Player AS player
    ON subq.PlayerID = player.PlayerID
WHERE subq.EventName LIKE '%upgrade%'
  AND subq.EventName LIKE '%gift%'
  AND player.UniversalPlayerID = '{uid}'
  AND subq.Returned IS NULL
"""

    tier_points_query = f"""
SELECT
    universalplayerid AS UniversalPlayerID,
    gamingdate,
    tierpoints
FROM dwd.dwd_mkt_pointbalance
WHERE universalplayerid = '{uid}'
  AND gamingdate >= '{start_date}'
  AND tierpoints >= {tier_rule['point_threshold']}
ORDER BY gamingdate DESC
"""

    return {
        "tierhist": tier_history_query.strip(),
        "prize_red": prize_red_query.strip(),
        "res": tier_points_query.strip(),
    }


def get_tier_history_result(query):
    loader = SQL("ENGAGE").get_loader()
    result = loader.load_data(query)
    if result.empty:
        return result.reindex(columns=TIER_HISTORY_COLUMNS)
    result = result.copy()
    if "CreatedDate" in result.columns:
        result["CreatedDate"] = result["CreatedDate"].astype(str)
    return result


def get_prize_red_result(query):
    """Return the reference script's `prize_red` dataframe."""
    loader = SQL("ENGAGE").get_loader()
    prize_red = loader.load_data(query)

    if prize_red.empty:
        return prize_red.reindex(columns=PRIZE_RED_COLUMNS)

    if "RedemptionGamingDate" in prize_red.columns:
        prize_red["RedemptionGamingDate"] = prize_red[
            "RedemptionGamingDate"
        ].astype(str)

    return prize_red


def get_tier_upgrade_result(query, tier=DEFAULT_TIER):
    """Return the reference script's `res` dataframe."""
    threshold = TIER_RULES[normalize_tier(tier)]["point_threshold"]
    loader = SQL("datamart").get_loader()
    tier_point_balance = loader.load_data(query)

    if tier_point_balance.empty:
        return tier_point_balance.reindex(columns=TIER_RESULT_COLUMNS)

    if "tierpoints" not in tier_point_balance.columns:
        raise ValueError("The tier-points query did not return a tierpoints column.")

    tier_points = pd.to_numeric(tier_point_balance["tierpoints"], errors="coerce")
    result = tier_point_balance.loc[tier_points >= threshold].copy()

    if "gamingdate" in result.columns:
        result["gamingdate"] = result["gamingdate"].astype(str)

    return result


def make_table(dataframe):
    return dash_table.DataTable(
        data=dataframe.to_dict("records"),
        columns=[{"name": column, "id": column} for column in dataframe.columns],
        page_size=15,
        sort_action="native",
        filter_action="native",
        style_table={"overflowX": "auto"},
        style_header={
            "backgroundColor": "#2c3e50",
            "color": "white",
            "fontWeight": "bold",
            "textAlign": "center",
        },
        style_cell={
            "padding": "8px",
            "textAlign": "center",
            "whiteSpace": "normal",
            "height": "auto",
        },
        style_data_conditional=[
            {"if": {"row_index": "odd"}, "backgroundColor": "#f5f7fa"},
        ],
    )


def _layout():
    return html.Div(
        className="container",
        children=[
            html.H1("Tier Upgrade Checker", className="title has-text-centered"),
            html.Div(
                className="box",
                style={"maxWidth": "520px", "margin": "0 auto 1.5rem"},
                children=[
                    html.Div(
                        className="field",
                        children=[
                            html.Label("UID", className="label"),
                            dcc.Input(
                                id="tier-upgrade-uid",
                                type="text",
                                placeholder="Enter UID",
                                className="input",
                                debounce=False,
                            ),
                        ],
                    ),
                    html.Div(
                        className="field",
                        children=[
                            html.Label("Tier", className="label", htmlFor="tier-upgrade-tier"),
                            dcc.Dropdown(
                                id="tier-upgrade-tier",
                                options=[{"label": tier, "value": tier} for tier in TIER_RULES],
                                value=DEFAULT_TIER,
                                clearable=False,
                                searchable=False,
                            ),
                            html.P(
                                "Supreme: at least 2,500 points. Maharlika: at least 15,000 points. "
                                "One upgrade gift per tier in a patron's lifetime.",
                                className="help",
                            ),
                        ],
                    ),
                    html.Div(
                        className="field",
                        children=[
                            html.Label(
                                "Gaming start year", className="label", htmlFor="tier-upgrade-year"
                            ),
                            dcc.Dropdown(
                                id="tier-upgrade-year",
                                options=[
                                    {"label": str(year), "value": year}
                                    for year in range(date.today().year, 1899, -1)
                                ],
                                value=date.today().year,
                                clearable=False,
                                searchable=True,
                            ),
                            html.P("Filters from January 1 of the selected year.", className="help"),
                        ],
                    ),
                    html.Button(
                        "Check",
                        id="tier-upgrade-check-button",
                        className="button is-info",
                        n_clicks=0,
                    ),
                ],
            ),
            dcc.Store(id="tier-upgrade-request"),
            html.Div(id="tier-upgrade-status", className="mb-3"),
            dcc.Loading(html.Div(id="tier-upgrade-tier-history-result", className="mb-5")),
            dcc.Loading(html.Div(id="tier-upgrade-result")),
            dcc.Loading(
                html.Div(id="tier-upgrade-prize-red-result", className="mt-5")
            ),
        ],
    )


def layout():
    if current_user.is_authenticated and has_access(current_user, TIER_UPGRADE_CHECKER):
        return _layout()
    return html.Div("No Access!")


@callback(
    Output("tier-upgrade-status", "children"),
    Output("tier-upgrade-request", "data"),
    Input("tier-upgrade-check-button", "n_clicks"),
    State("tier-upgrade-uid", "value"),
    State("tier-upgrade-year", "value"),
    State("tier-upgrade-tier", "value"),
    prevent_initial_call=True,
)
def check_tier_upgrade(n_clicks, uid_value, start_year_value, tier_value):
    try:
        uid = normalize_uid(uid_value)
        start_year = normalize_start_year(start_year_value)
        tier = normalize_tier(tier_value)
    except ValueError as exc:
        return html.P(str(exc), className="has-text-warning"), None

    # Result callbacks consume this snapshot independently. Including the
    # click count also lets users repeat a lookup for the same UID.
    return "", {
        "uid": uid,
        "start_year": start_year,
        "tier": tier,
        "request_id": n_clicks,
    }


def render_lookup_result(request, query_key, lookup, title, row_description):
    if not request:
        return None

    try:
        uid = normalize_uid(request["uid"])
        query = build_queries(uid, request["start_year"], request["tier"])[query_key]
        result = lookup(query)
    except Exception:
        logger.exception("Tier upgrade %s lookup failed", query_key)
        return html.Div(
            [
                html.H2(title, className="subtitle"),
                html.P(
                    f"Unable to retrieve {row_description}. Please try again.",
                    className="has-text-danger",
                ),
            ]
        )

    return html.Div(
        [
            html.H2(title, className="subtitle"),
            html.P(
                f"Found {len(result):,} {row_description} for {uid}.",
                className="has-text-success" if not result.empty else "has-text-grey",
            ),
            html.P("Empty dataframe", className="has-text-grey")
            if result.empty
            else None,
            make_table(result),
        ]
    )


@callback(
    Output("tier-upgrade-result", "children"),
    Input("tier-upgrade-request", "data"),
    prevent_initial_call=True,
)
def load_tier_upgrade_result(request):
    if not request:
        return None
    try:
        tier = normalize_tier(request["tier"])
    except (KeyError, ValueError) as exc:
        return html.P(str(exc), className="has-text-warning")
    threshold = TIER_RULES[tier]["point_threshold"]
    return render_lookup_result(
        request,
        "res",
        lambda query: get_tier_upgrade_result(query, tier),
        f"{tier} Tier Point Result (res)",
        f"tier-point row(s) at or above {threshold:,}",
    )


@callback(
    Output("tier-upgrade-tier-history-result", "children"),
    Input("tier-upgrade-request", "data"),
    prevent_initial_call=True,
)
def load_tier_history_result(request):
    if not request:
        return None
    return render_lookup_result(
        request,
        "tierhist",
        get_tier_history_result,
        "Tier Upgrade History",
        f"upgrade-history row(s) to {request.get('tier', '')}",
    )


@callback(
    Output("tier-upgrade-prize-red-result", "children"),
    Input("tier-upgrade-request", "data"),
    prevent_initial_call=True,
)
def load_prize_red_result(request):
    return render_lookup_result(
        request,
        "prize_red",
        get_prize_red_result,
        "Prize Redemption Result (prize_red)",
        "prize-redemption row(s)",
    )
