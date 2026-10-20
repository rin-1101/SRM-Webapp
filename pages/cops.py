import dash
from dash import Dash, dcc, html, dash_table, Input, Output, State, callback
import pandas as pd
from io import BytesIO
import base64

# Application Imports
from utils.paths import COPS_PATH

# Authentication Imports
from flask_login import current_user
from utils.login_handler import require_login, has_access, restricted_page

# Internal Imports
import sys

ROOT = "\\\\ominfstdpsd10001p-fs.int.okadamanila.com\\Casino\\Strategic Marketing\\Database Admin\\ETL\\Applications"
sys.path.append(f"{ROOT}\\okada\\")
from okada import SQL
from okada import LogService

logger = LogService("cops").get_logger()


def format_amount(x):
    if x >= 1_000_000:
        return f'{x / 1_000_000:.2f}M'
    elif x >= 1_000:
        return f'{x / 1_000:.1f}K'
    else:
        return f'{x:.0f}'


def get_cops(uid):
    from datetime import date, timedelta
    loader = SQL("datamart").get_loader()
    yesterday_date = date.today() - timedelta(1)
    query = f"""
    SELECT 
        c.universalplayerid as universalplayerid,
        mpt.fullname,
        c.eventname as event,
        c.system as system,
        c.earningrequired as earningrequired,
        c.fromdate_redeem as redemption_start,
        c.todate_redeem as redemption_end,
        CASE WHEN c.status='Redeemed' THEN 'Redeemed' ELSE 'Qualified/Invited' END as `status`,
        mb.adt_last12 as adt, mb.daysinactive as daysinactive, mb.lastplaydate as lastplaydate, mpt.hostname_mass as hostname
    FROM dws.dws_mkt_cops c 
    LEFT JOIN dws.dws_mkt_memberprofile mpt
        ON c.universalplayerid = mpt.uid
    LEFT JOIN dws.dws_mkt_memberbuild_test mb
        ON c.universalplayerid = mb.universalplayerid
    WHERE c.gd >= '{yesterday_date}'
    AND mb.gamingdate = '{yesterday_date}'
    AND mpt.uid = '{uid}'
    """
    logger.info(f"{current_user.id} has executed \n {query}")
    try:
        df = loader.load_data(query)
        df["adt"] = df["adt"].apply(format_amount)
    except Exception as e:
        logger.error(f"Error loading COPS data: {e}")
        return pd.DataFrame()  # Return an empty DataFrame on error

    return df


def get_mpt(uid):
    from datetime import date, timedelta
    loader = SQL("datamart").get_loader()
    yesterday_date = date.today() - timedelta(1)
    query = f"""
    SELECT 
        mpt.uid,
        mpt.fullname,
        mb.adt_last12 as adt, mb.daysinactive as daysinactive, mb.lastplaydate as lastplaydate, mpt.hostname_mass as hostname
    FROM dws.dws_mkt_memberprofile mpt
    LEFT JOIN dws.dws_mkt_memberbuild mb
        ON mpt.uid = mb.universalplayerid
    WHERE mb.gamingdate = '{yesterday_date}'
    AND mpt.uid = '{uid}'
    """
    logger.info(f"{current_user.id} has executed \n {query}")
    try:
        df = loader.load_data(query)
        df["adt"] = df["adt"].apply(format_amount)
    except Exception as e:
        logger.error(f"Error loading MPT data: {e}")
        return pd.DataFrame()  # Return an empty DataFrame on error

    return df


dash.register_page(__name__, path="/cops")
require_login(__name__, access_level=restricted_page[COPS_PATH]["access_level"])


def layout():
    if current_user.is_authenticated and has_access(current_user, COPS_PATH):
        logger.info(f"{current_user.id} has accessed")
        return _layout()
    else:
        return html.Div(["No Access!"])


def _layout():
    from datetime import date, timedelta
    yesterday_date = date.today() - timedelta(1)
    return html.Div(
        children=[
            html.H1("COPS Dashboard", className="title"),
            html.Br(),
            html.P(f"Data is updated as of {yesterday_date}"),
            html.Br(),
            html.Div(
                className="box has-shadow",
                style={"border-radius": "8px", "padding": "20px", "margin": "20px"},
                children=[
                    html.Form(
                        style={'width': '50%'},
                        children=[
                            html.Label('UniversalPlayerID:', className="label"),
                            dcc.Input(id='cops-uid', type='text', placeholder='Enter OM Number', className="input", style={'width': '100%'}),
                            html.Br(),
                            html.Div(id="cops-hostname", className="label"),
                            html.Div(id="cops-name", className="label"),
                            html.H1(id="cops-adt", className="label"),
                            html.H1(id="cops-daysinactive", className="label"),
                            html.H1(id="cops-lastplaydate", className="label"),
                            html.Button('Submit', id='submit-button', n_clicks=0, className="button is-primary", type="button"),
                        ]
                    ),
                ]
            ),
            dcc.Loading(html.Div(id="output-data_cops"))
        ]
    )


@callback(
    Output('cops-hostname', 'children'),
    Output('cops-name', 'children'),
    Output('cops-adt', 'children'),
    Output('cops-daysinactive', 'children'),
    Output('cops-lastplaydate', 'children'),
    Output('output-data_cops', 'children'),
    Input('submit-button', 'n_clicks'),
    State('cops-uid', 'value')
)
def update_table(n_clicks, uid):
    if n_clicks and n_clicks > 0:
        filtered_df = get_cops(uid)
        if filtered_df.empty:
            mpt = get_mpt(uid)
            if not mpt.empty:
                _hostname = mpt["hostname"].iloc[0]
                _name = mpt["fullname"].iloc[0]
                _adt = mpt["adt"].iloc[0]
                _daysinactive = mpt["daysinactive"].iloc[0]
                _lastplaydate = mpt["lastplaydate"].iloc[0]
                logger.info(f"Retrieved MPT data: {_hostname}, {_name}, {_adt}, {_daysinactive}, {_lastplaydate}")
                return f"Team: {_hostname}", f"Name: {_name}", f"ADT: {_adt}", f"DaysInactive: {_daysinactive}", f"LastPlayDate: {_lastplaydate}","Player has no offer to redeem"
            
        else:
            logger.info(filtered_df)
            filtered_df["redemption_start"] = pd.to_datetime(filtered_df["redemption_start"]).dt.strftime("%Y-%m-%d %I:%M %p")
            filtered_df["redemption_end"] = pd.to_datetime(filtered_df["redemption_end"]).dt.strftime("%Y-%m-%d %I:%M %p")
            _hostname = filtered_df["hostname"][0]
            _name = filtered_df["fullname"][0]
            _adt = filtered_df["adt"][0]
            _daysinactive = filtered_df["daysinactive"][0]
            _lastplaydate = filtered_df["lastplaydate"][0]
            _df = filtered_df[["event", "system", "status", "redemption_start", "redemption_end", "earningrequired"]]
            tbl = html.Div(
                [
                    dash_table.DataTable(
                        data=_df.to_dict("records"),
                        columns=[{"name": i, "id": i} for i in _df.columns],
                        page_size=10  # Example: set pagination
                    ),
                ]
            )
            return f"Team: {_hostname}", f"Name: {_name}", f"ADT: {_adt}", f"DaysInactive: {_daysinactive}", f"LastPlayDate: {_lastplaydate}", tbl
    return "", "", "", "", "", ""
