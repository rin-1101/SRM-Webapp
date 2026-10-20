import dash
from dash import Dash, dcc, html, dash_table, Input, Output, State, callback
import pandas as pd
from io import BytesIO, StringIO
import base64

# Application Imports
from utils.paths import REDEMPTION_PATH

# Authentication Imports
from flask_login import current_user
from utils.login_handler import require_login, has_access, restricted_page

# Internal Imports
import sys

ROOT = "\\\\ominfstdpsd10001p-fs.int.okadamanila.com\\Casino\\Strategic Marketing\\Database Admin\\ETL\\Applications"
sys.path.append(f"{ROOT}\\okada\\")
from okada import SQL
from okada import LogService

logger = LogService("redemption-dashboard").get_logger()


def get_redemption(start, end, event_name, preview=True):
    event_name = (event_name or "").strip()
    loader = SQL("datamart").get_loader()
    eng_loader = SQL("engage").get_loader()
    
    _limit = "LIMIT 5" if preview else "LIMIT 10000"
    query = f"""
SELECT
    universalplayerid AS universalplayerid,
    eventname AS eventname,
    prizename AS prizename,
    prizedesc AS prizedesc,
    prizevalue AS prizevalue,
    redemptionamount AS redemptionamount,
    bucketrequired AS bucketrequired,
    redemptiondate AS redemptiondate,
    redemptiongamedate AS redemptiongamedate,
    redeemedby AS redeemedby,
    returned AS returned,
    returneddate AS returneddate,
    returnedby AS returnedby,
    voucherno AS voucherno,
    config_sys AS config_sys
FROM dwd.dwd_mkt_promoredemption
WHERE upper(eventname) LIKE '%{event_name.upper()}%'
AND redemptiongamedate BETWEEN  '{start}' AND '{end}'
    """
    
    logger.info(query)
    # logger.info(f"{current_user.id} has executed \n {query}")
    df = loader.load_data(query)
    df["redemptiondate"] = pd.to_datetime(df["redemptiondate"])

    coded = loader.load_data("SELECT uid as universalplayerid, hostname_mass as hostname_mass, nationality as nationality FROM dws.dws_mkt_memberprofile")
    df = df.merge(coded,on="universalplayerid",how="left")
    halo_df = df[df['config_sys']=='Halo']
    query2 = f"""
        select 
        pr.id as voucherno, o.Comments, r.OverrideReason
        from engagedb.awa.UC_PL_PrizeRedemption pr
        join engagedb.awa.UC_X_EventDefinition ed on pr.EventDefinitionID = ed.id 
        join engagedb.dbo.UC_L_OverrideLog o on pr.id = o.TransactionID
        join engagedb.dbo.UC_X_OverrideReason r on o.ReasonID = r.id 
        where pr.id in {tuple(halo_df['voucherno'])}
        order by pr.ID desc
    """
    logger.info(query2)
    comments_df = eng_loader.load_data(query2)
    if len(comments_df) >0:
        comments_df["voucherno"] = (
            comments_df["voucherno"]
            .astype(str)
            .str.strip()
        )
        df["voucherno"] = (
            df["voucherno"]
            .astype(str)
            .str.strip()
        )
        df = df.merge(comments_df,on="voucherno",how="left")

    return df


dash.register_page(__name__, path=REDEMPTION_PATH)
require_login(__name__, access_level=restricted_page[REDEMPTION_PATH]["access_level"])


def layout():
    """
    Important: Always include this in the page code.
    layout function will always be used by default as where the page layout will be taken from
    This is a workaround to prevent unwanted users from accessing the report when pressing BACK.
    """
    # return _layout()
    if current_user.is_authenticated and has_access(current_user, REDEMPTION_PATH):
        logger.info(f"{current_user.id} has accessed")
        return _layout()
    else:
        return html.Div(["No Access!"])


def _layout():
    return html.Div(
        [
            html.H1("Redemption Report:", className="title"),
            html.Div(
                style={
                    "display": "flex",
                    "justify-content": "center",
                    "padding": "20px 0",
                },
                children=[
                    html.Div(
                        id="redemption-form",
                        className="box",
                        style={ 
                            "width": "30%",
                            "border-radius": "10px",
                            "box-shadow": "5px 5px 5px grey",
                        },
                        children=[
                            html.Div(
                                className="field",
                                children=[
                                    html.Label(
                                        className="label",
                                        children="Redemption Start Date",
                                    ),
                                        # Start Date
                                        dcc.DatePickerSingle(
                                            id="start-date",
                                            display_format="YYYY-MM-DD",
                                            placeholder="Select start date",
                                            style={"width": "100%"},
                                        ),

                                ],
                            ),
                            html.Div(
                                className="field",
                                children=[
                                    html.Label(
                                        className="label",
                                        children="Redemption End Date",
                                    ),
                                    
                                    # End Date
                                    dcc.DatePickerSingle(
                                        id="end-date",
                                        display_format="YYYY-MM-DD",
                                        placeholder="Select end date",
                                        style={"width": "100%"},
                                    ),
                                ],
                            ),
                            html.Div(
                                className="field",
                                children=[
                                    html.Label(
                                        className="label", children="Event Name"
                                    ),
                                    dcc.Input(
                                        type="text",
                                        id="event-name",
                                        className="input",
                                    ),
                                ],
                            ),
                            html.Div(
                                className="field is-grouped",
                                children=[
                                    html.Div(
                                        className="control",
                                        children=[
                                            html.Button(
                                                "Submit",
                                                id="submit-button",
                                                type="submit",
                                                className="button is-info",
                                                n_clicks=0,
                                            )
                                        ],
                                    )
                                ],
                            ),
                        ],
                    )
                ],
            ),
            dcc.Store(id="redemption-data-store"),
            dcc.Download(id="download-data-redemption"),
            dcc.Loading(html.Div(id="output-data")),
        ]
    )


@callback(
    Output("output-data", "children"),
    Output("redemption-data-store", "data"),
    Input("submit-button", "n_clicks"),
    State("start-date", "date"),
    State("end-date", "date"),
    State("event-name", "value"),
)
def display_data(n_clicks, start_date, end_date, event_name):
    if n_clicks and n_clicks > 0:
        source = get_redemption(start_date, end_date, event_name)
        stored_data = source.to_json(date_format="iso", orient="records")
        df = pd.read_json(StringIO(stored_data), orient="records")
        return html.Div(
            [
                dash_table.DataTable(
                    df.to_dict("records"),
                    [{"name": i, "id": i} for i in df.columns],
                    page_size=5,
                    style_table={
                        "overflowX": "auto",
                        "maxWidth": "100%",
                    },
                    style_cell={
                        "minWidth": "140px",
                        "width": "140px",
                        "maxWidth": "260px",
                        "overflow": "hidden",
                        "textOverflow": "ellipsis",
                        "whiteSpace": "nowrap",
                    },
                ),
                html.Br(),
                html.Button(
                    "Export Data",
                    id="export-button",
                    className="button is-primary",
                    n_clicks=0,
                ),
                html.Br(),
            ]
        ), stored_data
    else:
        return "", None


@callback(
    Output("download-data-redemption", "data"),
    Input("export-button", "n_clicks"),
    State("start-date", "date"),
    State("end-date", "date"),
    State("event-name", "value"),
    State("redemption-data-store", "data"),
    prevent_initial_call=True,
)
def export_data(n_clicks, start_date, end_date, event_name, stored_data):
    if n_clicks and n_clicks > 0 and stored_data:
        source = pd.read_json(StringIO(stored_data), orient="records")
        event_label = (event_name or "").strip() or "Redemption"
        return dcc.send_data_frame(
            source.to_csv,
            filename=f"{event_label}_{start_date}_{end_date}.csv",
            index=False,
        )
