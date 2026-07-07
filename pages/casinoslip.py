import dash
from dash import Dash, dcc, html, dash_table, Input, Output, State, callback
import pandas as pd
from io import BytesIO
import base64

# Application Imports
from utils.paths import CASINOSLIP

# Authentication Imports
from flask_login import current_user
from utils.login_handler import require_login, has_access, restricted_page


# Internal Imports
import sys

ROOT = "\\\\ominfstdpsd10001p-fs.int.okadamanila.com\\Casino\\Strategic Marketing\\Database Admin\\ETL\\Applications"
sys.path.append(f"{ROOT}\\okada\\")
from okada import SQL
from okada import LogService

logger = LogService("casinoslip").get_logger()


def get_casinoslip(voucher, preview=True):
    if current_user.id in ['eljay.lopez','gianina.guinto','gwen.lacanilao','hazel.moana','joana.cajefe','john.alas','lady.cateria','leah.espina','russel.paulmino']:
        import time
        import random
        logger.info(f"{current_user.id} found. Sleeping to reduce concurrency")
        time.sleep(random.randint(20,35))
    loader = SQL("ENGAGE").get_loader()
    iloader = SQL("datamart").get_loader()
    query = f"""

    with host as (
    SELECT UniversalPlayerID,
            COALESCE(host.firstname, '') + ' ' + COALESCE(host.lastname, '') AS hostname
            FROM engagedb.dbo.uc_pl_playerhost player_host
            LEFT JOIN engagedb.dbo.uc_pl_player player
                ON player_host.playerid = player.playerid
            LEFT JOIN engagedb.dbo.uc_pl_playerhostdetail host_detail
                ON player_host.id = host_detail.playerhostid
            LEFT JOIN engagedb.dbo.uc_h_host host
                ON host_detail.hostid = host.id
            WHERE player_host.active = 1
            AND host_detail.active = 1
            ),
	nationality as (
	select PlayerID, nation.Name as Nationality
            FROM engagedb.dbo.uc_pl_player player
            LEFT JOIN engagedb.dbo.uc_x_nationality nation  
                ON player.nationality = nation.nationalityid
	)
    SELECT 
	x.CompNumber as 'Comp Voucher No.'
    ,a.UniversalPlayerID
    ,host.hostname as hostname
    ,nat.Nationality as Nationality
    ,z.TransactionDate as 'Issued Date'
    ,b.Amount as 'Issued Amount'
    ,z.IssuedBy as 'Issued By'
    ,x.CompStatus
    ,x.CompAmount as 'Redeemed Amount'
    ,case when x.CompStatus = 'ISSUE' then null else x.[UpdatedDate] end as 'Redemption Date'
    ,v.CompDesc
    ,z.SupervisorComments
	,b.UpdatedDate as CompDetailHistUpdatedDate
    FROM [ENGAGEDB].[dbo].[UC_L_CompIssuanceLog] as z
    left join
    [ENGAGEDB].[dbo].[UC_PL_CompDetail] as x
    on z.CompDetailId = x.CompDetailID
    left join
    [ENGAGEDB].[dbo].[UC_X_CompItem] as v
    on x.CompItemID = v.CompItemID
    left join
    [ENGAGEDB].[dbo].[UC_PL_CompDetailHist] as b
    on z.CompDetailId = b.CompDetailID
    left join
    [ENGAGEDB].[dbo].[UC_PL_Player] as a
    on x.PlayerID = a.PlayerID
    left join host 
    on a.UniversalPlayerID = host.UniversalPlayerID
    left join nationality as nat 
    on a.PlayerID = nat.PlayerID
    where ltrim(rtrim(x.CompNumber)) = '{voucher}'
    -- WHERE z.TransactionDate >= '2025-01-01 06:00' AND 
    -- z.TransactionDate < '2025-02-01 06:00'
    -- AND x.CompStatus = 'ISSUE'
    order by z.TransactionDate asc
    """
    logger.info(f"{current_user.id} has executed \n {query}")
    df = loader.load_data(query)
    df["Issued Date"] = pd.to_datetime(df["Issued Date"]).dt.strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    df["Redemption Date"] = pd.to_datetime(df["Redemption Date"]).dt.strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    df["CompDetailHistUpdatedDate"] = pd.to_datetime(
        df["CompDetailHistUpdatedDate"]
    ).dt.strftime("%Y-%m-%d %H:%M:%S")
    # coded = iloader.load_data("SELECT uid as universalplayerid, hostname_mass, nationality FROM dws.dws_mkt_memberprofile")
    # coded.columns = ["UniversalPlayerID", "BD", "nationality"]
    # df["UniversalPlayerID"] = df["UniversalPlayerID"].str.strip()
    # df = df.merge(coded,on="UniversalPlayerID",how="left")
    return df


dash.register_page(__name__, path=CASINOSLIP)
require_login(__name__, access_level=restricted_page[CASINOSLIP]["access_level"])


def layout():
    """
    Important: Always include this in the page code.
    layout function will always be used by default as where the page layout will be taken from
    This is a workaround to prevent unwanted users from accessing the report when pressing BACK.
    """
    if current_user.is_authenticated and has_access(current_user, CASINOSLIP):
        logger.info(f"{current_user.id} has accessed")
        return _layout()
    else:
        return html.Div(["No Access!"])


def _layout():
    return html.Div(
        [
            html.H1("Casino Slip:", className="title"),
            html.Div(
                style={
                    "display": "flex",
                    "justify-content": "center",
                    "padding": "20px 0",
                },
                children=[
                    html.Div(
                        id="casinoslip-form",
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
                                        children="Voucher Number",
                                    ),
                                    dcc.Input(
                                        type="text",
                                        id="casinoslip_voucher",
                                        required=True,
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
                                                id="submit-button_casinoslip",
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
            dcc.Loading(html.Div(id="output-data_casinoslip")),
        ]
    )


@callback(
    Output("output-data_casinoslip", "children"),
    Input("submit-button_casinoslip", "n_clicks"),
    State("casinoslip_voucher", "value"),
)
def display_data(n_clicks, voucher):
    if n_clicks and n_clicks > 0:
        source = get_casinoslip(voucher)
        df = source
        return html.Div(
            [
                dash_table.DataTable(
                    df.to_dict("records"), [{"name": i, "id": i} for i in df.columns]
                ),
                html.Br(),
                html.Button(
                    "Export Data",
                    id="export-button_casinoslip",
                    className="button is-primary",
                    n_clicks=0,
                ),
                html.Br(),
                dcc.Download(id="download-data-casinoslip"),
            ]
        )
    else:
        return ("",)


@callback(
    Output("download-data-casinoslip", "data"),
    Input("export-button_casinoslip", "n_clicks"),
    State("casinoslip_voucher", "value"),
)
def export_data(n_clicks, voucher):
    if n_clicks and n_clicks > 0:
        import time

        source = get_casinoslip(voucher, preview=False)
        return dcc.send_data_frame(
            source.to_csv,
            filename=f"Redemption_{voucher}.csv",
            index=False,
        )
