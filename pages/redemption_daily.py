import dash
from dash import Dash, dcc, html, dash_table, Input, Output, State, callback
import pandas as pd
from io import BytesIO
import base64

# Application Imports
from utils.paths import REDEMPTION_DAILY

# Authentication Imports
from flask_login import current_user
from utils.login_handler import require_login, has_access, restricted_page

# Internal Imports
import sys

ROOT = "\\\\ominfstdpsd10001p-fs.int.okadamanila.com\\Casino\\Strategic Marketing\\Database Admin\\ETL\\Applications"
sys.path.append(f"{ROOT}\\okada\\")
from okada import SQL
from okada import LogService

logger = LogService("redemptiondaily-dashboard").get_logger()


def get_redemption(gdate, preview=True):
    loader = SQL("datamart").get_loader()
    _limit = "LIMIT 5" if preview else ""
    query = f"""
    SELECT universalplayerid, eventname, 
    prizename, prizedesc, prizevalue, redemptionamount, bucketrequired, 
    redemptiondate, redemptiongamedate, redeemedby, returned, returneddate, returnedby, voucherno, config_sys
    FROM dwd.dwd_mkt_promoredemption
    WHERE redemptiongamedate =  '{gdate}'
    {_limit}
    """
    # logger.info(f"{current_user.id} has executed \n {query}")
    df = loader.load_data(query)
    df["redemptiondate"] = pd.to_datetime(df["redemptiondate"])
    return df


dash.register_page(__name__, path=REDEMPTION_DAILY)
require_login(__name__, access_level=restricted_page[REDEMPTION_DAILY]["access_level"])


def layout():
    """
    Important: Always include this in the page code.
    layout function will always be used by default as where the page layout will be taken from
    This is a workaround to prevent unwanted users from accessing the report when pressing BACK.
    """
    return _layout()
    if current_user.is_authenticated and has_access(current_user, REDEMPTION_DAILY):
        logger.info(f"{current_user.id} has accessed")
        return _layout()
    else:
        return html.Div(["No Access!"])


def _layout():
    return html.Div(
        [
            html.H1("Redemption Daily:", className="title"),
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
                                        children="Redemption GamingDate",
                                    ),
                                    dcc.DatePickerSingle(
                                        id="start-date_reddaily",
                                        display_format="YYYY-MM-DD",
                                        placeholder="Select a date",
                                        style={"width": "100%"},
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
                                                id="submit-button_reddaily",
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
            dcc.Loading(html.Div(id="output-data_reddaily")),
        ]
    )


@callback(
    Output("output-data_reddaily", "children"),
    Input("submit-button_reddaily", "n_clicks"),
    State("start-date_reddaily", "date"),
)
def display_data(n_clicks, start_date_reddaily):
    if n_clicks and n_clicks > 0:
        source = get_redemption(start_date_reddaily)
        df = source.head(5)
        return html.Div(
            [
                dash_table.DataTable(
                    df.to_dict("records"), [{"name": i, "id": i} for i in df.columns]
                ),
                html.Br(),
                html.Button(
                    "Export Data",
                    id="export-button_reddaily",
                    className="button is-primary",
                    n_clicks=0,
                ),
                html.Br(),
                dcc.Download(id="download-data-redemption_reddaily"),
            ]
        )
    else:
        return ("",)


@callback(
    Output("download-data-redemption_reddaily", "data"),
    Input("export-button_reddaily", "n_clicks"),
    State("start-date_reddaily", "date"),
)
def export_data(n_clicks, start_date_reddaily):
    if n_clicks and n_clicks > 0:
        import time

        source = get_redemption(start_date_reddaily, preview=False)
        return dcc.send_data_frame(
            source.to_csv,
            filename=f"Redemption_{start_date_reddaily}.csv",
            index=False,
        )
