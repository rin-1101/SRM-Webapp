import sys
import dash
import pandas as pd
from dash import dcc, html, dash_table, Input, Output, State, callback, ctx, ALL
from utils.paths import COMMS
dash.register_page(__name__, path=COMMS)

# Internal Imports
import sys

ROOT = "\\\\ominfstdpsd10001p-fs.int.okadamanila.com\\Casino\\Strategic Marketing\\Database Admin\\ETL\\Applications"
sys.path.append(f"{ROOT}\\okada\\")
from okada import SQL
from okada import LogService

# logger = LogService("comms-dashboard").get_logger()


ROOT = "\\\\ominfstdpsd10001p-fs.int.okadamanila.com\\Casino\\Strategic Marketing\\Database Admin\\ETL\\Applications"
sys.path.append(f"{ROOT}\\okada\\")
sys.path.append(f"{ROOT}\\reports\\pages\\")

# Layout function
def layout():
    return html.Div(
        style={"display": "flex", "height": "100vh"},
        children=[

            # Link to specific CSS file for this layout
            html.Link(rel='stylesheet', href='/assets/main.css'),
            # Search Panel
            html.Div(
                style={
                    "width": "300px",
                    "padding": "20px",
                    "borderRight": "1px solid #ddd",
                    "backgroundColor": "#f7f7f7",
                },
                children=[
                    html.H2("Search", className="title is-4"),

                    html.Label("OM Number:", className="label"),
                    dcc.Input(id="om-number", type="text", className="input"),

                    html.Br(), html.Br(),

                    html.Label("Promotion:", className="label"),
                    dcc.Input(id="promotion", type="text", className="input"),

                    html.Br(), html.Br(),

                    html.Label("Start Date:", className="label"),
                    dcc.DatePickerSingle(
                        id="start-date",
                        date=pd.Timestamp.today() - pd.Timedelta(days=30),
                    ),

                    html.Br(), html.Br(),

                    html.Label("End Date:", className="label"),
                    dcc.DatePickerSingle(
                        id="end-date",
                        date=pd.Timestamp.today(),
                    ),

                    html.Br(), html.Br(),
                    html.Button(
                        "Search",
                        id="search-btn",
                        className="button is-primary is-fullwidth",
                    ),
                ],
            ),

            # Data Table
            html.Div(
                style={"flex": "1", "padding": "30px", "overflowY": "auto"},
                children=[
                    html.H1("Comms Dashboard", className="title is-2"),

                    dash_table.DataTable(
                        id="sms-table",
                        style_table={"height": "400px", "overflowY": "auto"},
                        filter_action="native",
                        columns=[
                            {"name": "UniversalPlayerID", "id": "UniversalPlayerID"},
                            {"name": "First Name", "id": "FirstName"},
                            {"name": "Promotion Name", "id": "PromotionName"},
                            {"name": "Event ID", "id": "EventID"},
                            {"name": "Mobile Number", "id": "Mobile"},
                            {"name": "Channel", "id": "Channel"},
                            {"name": "Prize", "id": "Prize"},
                            {"name": "BlastDate", "id": "BlastDate"},
                        ],
                        data=[],
                        active_cell=None,   # ← replaces row_selectable + selected_rows
                        page_size=11,
                    ),

                    # Hidden Stores
                    dcc.Store(id="sms-results-store"),
                    dcc.Store(id="selected-sms-store"),

                    # Modal
                    html.Div(
                        id="sms-modal",
                        className="modal",
                        children=[
                            html.Div(className="modal-background", id="modal-close-bg"),
                            html.Div(
                                className="modal-card",
                                children=[
                                    html.Header(
                                        className="modal-card-head",
                                        children=[
                                            html.P("SMS Content", className="modal-card-title"),
                                            html.Button(className="delete", id="modal-close-x"),
                                        ],
                                    ),
                                    html.Section(
                                        id="sms-modal-body",
                                        className="modal-card-body",
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )

# Helper Functions
import yaml
def get_html(event_id, first_name="",uid=""):
    jhtml_path = fr"\\ominfstdpsd10001p-fs.int.okadamanila.com\Casino\Strategic Marketing\Database Admin\ETL\Applications\reports\documents\EDM\{event_id}.html"
    try:
        with open(jhtml_path, "r", encoding="utf-8") as f:
            html_content = f.read()
            # Replace placeholder before returning
            if first_name:
                html_content = html_content.replace("[first_name]", first_name)
                html_content = html_content.replace("[cc_memberid]", uid)
                
            return html.Iframe(
                srcDoc=html_content,
                style={"width": "100%","height":"100%"}  # optional inline style for 80vw width
            )
    except FileNotFoundError:
        return html.Div("EDM content not available")

def load_placeholder_map(path=r"\\ominfstdpsd10001p-fs.int.okadamanila.com\Casino\Strategic Marketing\Database Admin\ETL\Applications\reports\config\comms.yaml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def set_parameters(sms_message, data, placeholder_map):
    final_message = sms_message
    for placeholder, field in placeholder_map.items():
        final_message = final_message.replace(
            placeholder,
            str(data.get(field, ""))
        )
    return final_message

def fetch_and_format_sms_data(om_number, promotion, start_date, end_date):
    """ Fetch and format the SMS data for the table. """
    start_date = pd.to_datetime(start_date) if start_date else None
    end_date = pd.to_datetime(end_date) if end_date else None
    
    from sms_etl.sms import SMS

    sms_processor = SMS()
    df = sms_processor.read_sms_blast(
        universalplayerid=om_number, 
        eventname=promotion, 
        startblastdate=start_date, 
        endblastdate=end_date
    )
    # logger.info(sql)
    if df.empty:
        return [], []
    records = df.to_dict("records")


    return records, records

# ================= SEARCH TABLE =================
@callback(
    Output("sms-table", "data"),
    Output("sms-results-store", "data"),
    Input("search-btn", "n_clicks"),
    State("om-number", "value"),
    State("promotion", "value"),
    State("start-date", "date"),
    State("end-date", "date"),
    prevent_initial_call=True,
)
def search_sms(_, om_number, promotion, start_date, end_date):
    """ Callback to search and update the table with SMS data. """
    if om_number is None or om_number == "":
        return [], []
    return fetch_and_format_sms_data(om_number, promotion, start_date, end_date)

@callback(
    Output("sms-modal", "className"),
    Output("sms-modal-body", "children"),
    Input("sms-table", "active_cell"),   # ← changed
    State("sms-results-store", "data"),
    prevent_initial_call=True,
)
def open_sms_from_row(active_cell, records):
    if not active_cell or not records:
        return dash.no_update, dash.no_update

    selected_index = active_cell["row"]  # ← active_cell gives you {"row": N, "column": N, ...}

    if selected_index >= len(records):
        return dash.no_update, dash.no_update

    selected_record = records[selected_index]

    EventName = selected_record.get("PromotionName")

    EventID = selected_record.get("EventID")

    channel = selected_record.get("Channel")
    
    if channel == "2": #EDM
        #modify to change parameters
        edm_content = get_html(EventID, selected_record.get("FirstName"), selected_record.get("UniversalPlayerID")) 
        return "modal is-active is-edm",edm_content #add class to make it 80vw

    if not EventName:
        return "modal is-active", html.Div("No SMS Found for this entry.", style={"whiteSpace": "pre-wrap"})

    from sms_etl.sms import SMS

    sms_processor = SMS()
    sample_text = selected_record.get("SMSContent")
    # placeholder_map = load_placeholder_map()
    # sample_text = set_parameters(sample_text, selected_record,placeholder_map)

    if not sample_text:
        sample_text = "No SMS content available."

    return "modal is-active", html.Div(str(sample_text), style={"whiteSpace": "pre-wrap"})

@callback(
    Output("sms-modal", "className", allow_duplicate=True),
    Input("modal-close-bg", "n_clicks"),
    Input("modal-close-x", "n_clicks"),
    prevent_initial_call=True,
)
def close_modal(_, __):
    """ Callback to close the modal when the background or close button is clicked. """
    if ctx.triggered_id:
        return "modal"
    return dash.no_update