# import dash
# from dash import dcc, html, Input, Output, no_update, callback, State, dash_table
# from flask_login import current_user
# from pages.login import layout as login_layout
# from utils.login_handler import get_accessible_pages_by_role, ACCOUNTS, require_login
# import plotly.express as px
# import pandas as pd
# from datetime import date, timedelta

# # Application Imports
# from utils.paths import OVERCOMP

# # Authentication Imports
# from flask_login import current_user
# from utils.login_handler import require_login, has_access, restricted_page

# dash.register_page(__name__, path=OVERCOMP)

# # Internal Imports
# import sys

# ROOT = "\\\\ominfstdpsd10001p-fs.int.okadamanila.com\\Casino\\Strategic Marketing\\Database Admin\\ETL\\Applications"
# sys.path.append(f"{ROOT}\\okada\\")
# sys.path.append(f"{ROOT}\\reports\\pages\\")

# PATH = f"{ROOT}\\overcomp"
# sys.path.append(f"{ROOT}\\okada\\")
# from okada import LogService

# logger = LogService("redemptiondaily-dashboard").get_logger()




# require_login(__name__, access_level=restricted_page[OVERCOMP]["access_level"])


# def layout():
#     """
#     Important: Always include this in the page code.
#     layout function will always be used by default as where the page layout will be taken from
#     This is a workaround to prevent unwanted users from accessing the report when pressing BACK.
#     """
#     if current_user.is_authenticated and has_access(current_user, OVERCOMP):
#         logger.info(f"{current_user.id} has accessed")
#         return _layout()
#     else:
#         return _layout()
#         return html.Div(["No Access!"])

# def _layout():
#     today = date.today()
#     diff = today.weekday()
#     monday = today - timedelta(diff)
#     overcomp = pd.read_csv(f"{PATH}\\overcomp_{monday}.csv")
#     df = overcomp.head()
#     test = dash_table.DataTable(
#                     df.to_dict("records"), [{"name": i, "id": i} for i in df.columns]
#                 )
#     return html.Div([
#         html.H1("Overcomp Report", className="title"),
#         test,
#         html.Br(),
#         html.Button("Export",id="export-button_overcomp",className="button is-info"),
#         html.Br(),
#         dcc.Download(id="download-data-overcomp"),
#     ])


# @callback(
#     Output("download-data-overcomp", "data"),
#     Input("export-button_overcomp", "n_clicks"),
# )
# def export_data_overcomp(n_clicks):
#     if n_clicks and n_clicks > 0:
#         today = date.today()
#         diff = today.weekday()
#         monday = today - timedelta(days=diff)
        
#         try:
#             overcomp = pd.read_csv(f"{PATH}\\overcomp_{monday}.csv")
#             return dcc.send_data_frame(
#                 overcomp.to_csv,
#                 filename=f"Overcomp_{monday}.csv",
#                 index=False,
#             )
#         except FileNotFoundError:
#             logger.error(f"CSV file for {monday} not found during export.")
#             return no_update


