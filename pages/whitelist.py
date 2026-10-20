import dash
import pandas as pd
from dash import dcc, html, dash_table, Input, Output, State, callback, ctx
from utils.paths import COMMS
import sys

ROOT = "\\\\ominfstdpsd10001p-fs.int.okadamanila.com\\Casino\\Strategic Marketing\\Database Admin\\ETL\\Applications"
sys.path.append(f"{ROOT}\\okada\\")
from okada import SQL
from okada import LogService

logger = LogService("comms-dashboard").get_logger()
# Authentication Imports
from flask_login import current_user
from utils.login_handler import require_login, has_access, restricted_page


from pages.patrondb_etl import (
    empty_placeholder,
    fetch_active_patron_offers,
    fetch_contactable_status,
    fetch_loadings_records,
    fetch_sms_records,
    filter_promotions,
    get_edm_content,
    make_contactable_table,
    make_table,
    search_patron_offers,
)

dash.register_page(__name__, path=COMMS)
require_login(__name__, access_level=restricted_page[COMMS]["access_level"])



def collapsible_section(section_id, title, subtitle, children):
    return html.Details(
        id=section_id,
        open=True,
        className="box mb-4",
        style={"padding": "0"},
        children=[
            html.Summary(
                style={
                    "cursor": "pointer",
                    "padding": "16px",
                    "listStyle": "none",
                    "borderBottom": "1px solid #edf0f3",
                },
                children=html.P(title, className="title is-5 mb-0"),
            ),
            html.Div(
                style={"padding": "16px"},
                children=[html.P(subtitle, className="is-size-7 mb-3"), dcc.Loading(html.Div(children=children))],
            ),
        ],
    )


def comms_layout():
    return html.Div(
        id="comms-content",
        children=[
            collapsible_section(
                "contactable-content",
                "Marketable and Non Marketable Reason",
                "Current Marketable status and non-marketable reason.",
                [
                    html.Div(id="contactable-container", children=empty_placeholder()),
                ],
            ),
            collapsible_section(
                "communications-content",
                "Communications",
                "SMS / EDM blast history for the selected patron and date range.",
                [
                    dash_table.DataTable(
                        id="sms-table",
                        style_table={"overflowY": "auto", "overflowX": "auto"},
                        style_header={
                            "fontWeight": "600",
                            "textAlign": "center",
                            "padding": "8px",
                        },
                        style_cell={
                            "fontFamily": "Segoe UI, Arial, sans-serif",
                            "fontSize": "12px",
                            "padding": "7px",
                            "textAlign": "center",
                            "whiteSpace": "normal",
                            "height": "auto",
                        },
                        filter_action="native",
                        columns=[
                            {"name": "UniversalPlayerID", "id": "UniversalPlayerID"},
                            {"name": "First Name", "id": "FirstName"},
                            {"name": "Promotion Name", "id": "PromotionName"},
                            {"name": "Floor Name", "id": "FloorName"},
                            {"name": "Event ID", "id": "EventID"},
                            {"name": "Mobile Number", "id": "Mobile"},
                            {"name": "Channel", "id": "Channel"},
                            {"name": "Prize", "id": "Prize"},
                            {"name": "BlastDate", "id": "BlastDate"},
                        ],
                        data=[],
                        active_cell=None,
                        page_size=11,
                    ),
                ],
            ),
            collapsible_section(
                "loadings-content",
                "Loadings",
                "HALo Web Service bucket adjustments for the selected patron and date range.",
                [
                    html.Div(id="loadings-table-container", children=empty_placeholder()),
                ],
            ),
            dcc.Store(id="sms-results-store"),
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
                                    html.P("Comms Content", className="modal-card-title"),
                                    html.Button(className="delete", id="modal-close-x"),
                                ],
                            ),
                            html.Section(id="sms-modal-body", className="modal-card-body"),
                        ],
                    ),
                ],
            ),
        ],
    )

def promotions_layout():
    return html.Div(
        id="promotions-content",
        children=[
            collapsible_section(
                "whitelist-offers-content",
                "Eligible Offers",
                "Assigned offers from the selected OM number.",
                [
                    html.Div(id="pt-patron-search-status", className="mb-3"),
                    html.Div(
                        id="pt-patron-result-block",
                        style={"display": "none"},
                        children=[
                            html.P(
                                "Eligible Offers",
                                className="has-text-info has-text-weight-semibold is-size-7 mb-2",
                                style={"textTransform": "uppercase", "letterSpacing": "0.05em"},
                            ),
                            html.Div(id="pt-offers-table-container", children=empty_placeholder()),
                        ],
                    ),
                ],
            ),
            collapsible_section(
                "active-promotions-content",
                "Active Promotions (Patron May or May not be Eligible)",
                "Search active campaign offers by promotion name.",
                [
                    html.Div(
                        className="field is-grouped mb-4",
                        children=[
                            html.Div(
                                className="control is-expanded",
                                children=[
                                    dcc.Input(
                                        id="pt-promo-search-input",
                                        type="text",
                                        placeholder="Enter Promotion Name",
                                        className="input is-small",
                                        debounce=True,
                                    ),
                                ],
                            ),
                            html.Div(
                                className="control",
                                children=[
                                    html.Button(
                                        "Search Promotion",
                                        id="pt-promo-search-button",
                                        className="button is-info is-small",
                                        n_clicks=0,
                                    ),
                                ],
                            ),
                        ],
                    ),
                    html.Div(id="pt-promo-table-container"),
                    html.P("Showing active promotions only.", className="has-text-grey is-size-7 mt-3"),
                ],
            ),
        ],
    )
    

def layout():
    if current_user.is_authenticated and has_access(current_user, COMMS):
        logger.info(f"{current_user.id} has accessed")
        return _layout()
    else:
        return html.Div(["No Access!"])

def _layout():
    return html.Div(
        style={
            "display": "flex",
            "minHeight": "100vh",
            "overflow": "hidden",
            "fontFamily": "Segoe UI, Arial, sans-serif",
        },
        children=[
            html.Link(rel="stylesheet", href="/assets/main.css"),
            html.Div(
                style={
                    "width": "300px",
                    "flex": "0 0 300px",
                    "padding": "20px",
                    "borderRight": "1px solid #ddd",
                },
                children=[
                    html.Div(
                        style={"marginBottom": "18px", "textAlign": "center"},
                        children=[
                            html.P("Patron DB", style={"fontSize": "20px", "fontWeight": "600", "marginBottom": "2px"}),
                            html.P("Comms & whitelist lookup", style={"fontSize": "12px"}),
                        ],
                    ),
                    html.Label("OM Number", className="label is-small"),
                    dcc.Input(
                        id="om-number",
                        type="text",
                        placeholder="Enter OM Number",
                        className="input is-small mb-4",
                        style={"width": "100%"},
                    ),
                    html.Label("Start Date", className="label is-small"),
                    dcc.DatePickerSingle(
                        id="start-date",
                        date=pd.Timestamp.today() - pd.Timedelta(days=14),
                        style={"width": "100%"},
                    ),
                    html.Br(),
                    html.Br(),
                    html.Label("End Date", className="label is-small"),
                    dcc.DatePickerSingle(id="end-date", date=pd.Timestamp.today(), style={"width": "100%"}),
                    html.Br(),
                    html.Br(),
                    html.Button(
                        "Search",
                        id="search-btn",
                        className="button is-primary is-fullwidth is-small",
                        style={"height": "36px", "fontWeight": "600"},
                    ),
                ],
            ),
            html.Div(
                style={"flex": "1", "padding": "20px", "overflowY": "auto"},
                children=[
                    html.Div(
                        className="mb-4",
                        style={"textAlign": "center"},
                        children=[
                            html.H1("Patron Engagement Dashboard", className="title is-4 mb-1"),
                            html.P("Search once to refresh communications, patron whitelist details, and promotion data.", className="is-size-7"),
                        ],
                    ),
                    comms_layout(),
                    promotions_layout(),
                ],
            ),
        ],
    )


@callback(
    Output("sms-table", "data"),
    Output("sms-results-store", "data"),
    Input("search-btn", "n_clicks"),
    State("om-number", "value"),
    State("start-date", "date"),
    State("end-date", "date"),
    prevent_initial_call=True,
)
def search_sms(_, om_number, start_date, end_date):
    return fetch_sms_records(om_number, None, start_date, end_date)


@callback(
    Output("loadings-table-container", "children"),
    Input("search-btn", "n_clicks"),
    State("om-number", "value"),
    State("start-date", "date"),
    State("end-date", "date"),
    prevent_initial_call=True,
)
def search_loadings(_, om_number, start_date, end_date):
    return make_table(fetch_loadings_records(om_number, start_date, end_date), "loadings-table", page_size=8)


@callback(
    Output("contactable-container", "children"),
    Input("search-btn", "n_clicks"),
    State("om-number", "value"),
    prevent_initial_call=True,
)
def search_contactable(_, om_number):
    return make_contactable_table(fetch_contactable_status(om_number), "contactable-table", page_size=5)


@callback(
    Output("sms-modal", "className"),
    Output("sms-modal-body", "children"),
    Input("sms-table", "active_cell"),
    State("sms-table", "derived_viewport_data"),
    State("sms-results-store", "data"),
    prevent_initial_call=True,
)
def open_sms_from_row(active_cell, viewport_records, records):
    if not active_cell or not records:
        return dash.no_update, dash.no_update

    selected_index = active_cell["row"]
    visible_records = viewport_records or records
    if selected_index >= len(visible_records):
        return dash.no_update, dash.no_update

    selected_record = visible_records[selected_index]
    event_name = selected_record.get("PromotionName")
    event_id = selected_record.get("EventID")
    channel = selected_record.get("Channel")

    if channel == "2":
        edm_content = get_edm_content(
            event_id,
            selected_record.get("FirstName"),
            selected_record.get("UniversalPlayerID"),
        )
        return "modal is-active is-edm", edm_content

    if not event_name:
        return "modal is-active", html.Div("No SMS Found for this entry.", style={"whiteSpace": "pre-wrap"})

    sample_text = selected_record.get("SMSContent") or "No SMS content available."
    return "modal is-active", html.Div(str(sample_text), style={"whiteSpace": "pre-wrap"})


@callback(
    Output("sms-modal", "className", allow_duplicate=True),
    Input("modal-close-bg", "n_clicks"),
    Input("modal-close-x", "n_clicks"),
    prevent_initial_call=True,
)
def close_modal(_, __):
    if ctx.triggered_id:
        return "modal"
    return dash.no_update


@callback(
    Output("pt-offers-table-container", "children"),
    Output("pt-patron-search-status", "children"),
    Output("pt-patron-result-block", "style"),
    Input("search-btn", "n_clicks"),
    State("om-number", "value"),
    State("start-date", "date"),
    State("end-date", "date"),
    prevent_initial_call=True,
)
def search_patron(n_clicks, om_input, start_date, end_date):
    hidden = {"display": "none"}
    visible = {"display": "block"}
    blanks = (empty_placeholder(),)

    if not om_input or not om_input.strip():
        msg = html.Span("Please enter an OM Number.", className="has-text-warning is-size-7")
        return (*blanks, msg, hidden)

    patron, _, uid = search_patron_offers(om_input)
    if patron is None:
        msg = html.Span(f"No patron found for '{uid}'.", className="has-text-danger is-size-7")
        return (*blanks, msg, hidden)

    offers = fetch_active_patron_offers(uid, start_date, end_date)
    offers_table = make_table(offers, "pt-offers-table", page_size=5)
    msg = html.Span(f"Loaded patron: {uid}", className="has-text-success is-size-7")

    return (
        offers_table,
        msg,
        visible,
    )


@callback(
    Output("pt-promo-table-container", "children"),
    Input("pt-promo-search-button", "n_clicks"),
    Input("pt-promo-search-input", "value"),
    State("end-date", "date"),
    prevent_initial_call=False,
)
def search_promos(n_clicks, query, end_date):
    return make_table(filter_promotions(query, end_date), "pt-promo-results-table")
