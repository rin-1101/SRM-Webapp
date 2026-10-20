import dash
from dash import Dash, no_update, dcc, html, dash_table, Input, Output, State, callback
import pandas as pd
from io import BytesIO, StringIO
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
    eng_loader = SQL("engage").get_loader()
    _limit = ""
    query = f"""
    SELECT universalplayerid, eventname, 
    prizename, prizedesc, prizevalue, redemptionamount, bucketrequired, 
    redemptiondate, redemptiongamedate, redeemedby, returned, returneddate, returnedby, voucherno, config_sys
    FROM dwd.dwd_mkt_promoredemption
    WHERE redemptiongamedate =  '{gdate}'
    {_limit}
    """
    logger.info(query)
    # logger.info(f"{current_user.id} has executed \n {query}")
    df = loader.load_data(query)
    df["redemptiondate"] = pd.to_datetime(df["redemptiondate"])

    halo_df = df[df["config_sys"] == "Halo"]
    query2 = f"""
        select 
        pr.id as voucherno, o.Comments, r.OverrideReason
        from engagedb.awa.UC_PL_PrizeRedemption pr
        join engagedb.awa.UC_X_EventDefinition ed on pr.EventDefinitionID = ed.id 
        join engagedb.dbo.UC_L_OverrideLog o on pr.id = o.TransactionID
        join engagedb.dbo.UC_X_OverrideReason r on o.ReasonID = r.id 
        where pr.id in {tuple(halo_df["voucherno"])}
        order by pr.ID desc
    """
    logger.info(query2)
    comments_df = eng_loader.load_data(query2)
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
    df = df.merge(comments_df, on="voucherno", how="left")

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
            dcc.Store(id="redemption-daily-data-store"),
            dcc.Download(id="download-data-redemption_reddaily"),
            dcc.Loading(html.Div(id="output-data_reddaily")),
        ]
    )

@callback(
    Output("output-data_reddaily", "children"),
    Output("download-data-redemption_reddaily", "data"),
    Input("submit-button_reddaily", "n_clicks"),
    State("start-date_reddaily", "date"),
    prevent_initial_call=True,
)
def display_and_download(n_clicks, start_date_reddaily):

    if n_clicks and n_clicks > 0:

        # Get data only once
        df = get_redemption(start_date_reddaily)

        # Create table
        table = dash_table.DataTable(
            data=df.to_dict("records"),
            columns=[
                {"name": i, "id": i}
                for i in df.columns
            ],
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
        )

        # Create CSV download
        download = dcc.send_data_frame(
            df.to_csv,
            filename=f"Redemption_{start_date_reddaily}.csv",
            index=False,
        )

        return table, download

    return "", no_update