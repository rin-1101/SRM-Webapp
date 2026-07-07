import dash
from dash import dcc, html, dash_table, Input, Output, State, callback
import pandas as pd

dash.register_page(__name__, path="/promotions-tracker")


# ─── Sample Data ─────────────────────────────────────────────────────────────
# Replace these DataFrames with real DB/API queries.

# 1. Patron Details — one row per patron
DF_PATRONS = pd.DataFrame([
    {"uid": "OM1", "name": "Juan Dela Cruz", "tier": "Premium", "birthdate": "March 15, 1980"},
    {"uid": "OM-87654321", "name": "Maria Santos",   "tier": "Elite",   "birthdate": "July 22, 1975"},
])

# 2. Patron Offers — one row per offer; a patron can have multiple
DF_OFFERS = pd.DataFrame([
    {
        "uid":            "OM1",
        "offer_name":     "Premium Play & Stay",
        "offer_type":     "Gaming + Hotel",
        "reward":         "PHP 5,000 Free Play",
        "validity":       "Jun 1 – Jun 30, 2025",
        "offer_details":  "PHP 5,000 Free Play • 1 Complimentary Room Night • Dining Voucher",
        "status":         "ACTIVE",
    },
    {
        "uid":            "OM1",
        "offer_name":     "Weekend Bonus",
        "offer_type":     "Bonus",
        "reward":         "2x Points Multiplier",
        "validity":       "May 10 – May 31, 2025",
        "offer_details":  "Double points every Saturday and Sunday",
        "status":         "ACTIVE",
    },
    {
        "uid":            "OM-87654321",
        "offer_name":     "Summer Cashback",
        "offer_type":     "Cashback",
        "reward":         "15% Cashback",
        "validity":       "May 15 – Jun 15, 2025",
        "offer_details":  "15% Cashback on Gaming • PHP 2,000 F&B Credit",
        "status":         "ACTIVE",
    },
])

# 3. Promotions List — master list of all active promotions
DF_PROMOTIONS = pd.DataFrame([
    {
        "offer_name":    "Premium Play & Stay",
        "offer_type":    "Gaming + Hotel",
        "active_period": "Jun 1 – Jun 30, 2025",
        "status":        "ACTIVE",
        "summary":       "PHP 5,000 FP + Room + Dining",
    },
    {
        "offer_name":    "Summer Cashback",
        "offer_type":    "Cashback",
        "active_period": "May 15 – Jun 15, 2025",
        "status":        "ACTIVE",
        "summary":       "15% Cashback + PHP 2,000 F&B",
    },
    {
        "offer_name":    "Weekend Bonus",
        "offer_type":    "Bonus",
        "active_period": "May 10 – May 31, 2025",
        "status":        "ACTIVE",
        "summary":       "2x Points every Sat & Sun",
    },
])


# ─── Helpers ─────────────────────────────────────────────────────────────────

def detail_field(label: str, field_id: str) -> html.Div:
    """Label on left, value on right — matches patron.py style."""
    return html.Div(
        className="is-flex is-justify-content-space-between mb-2",
        style={"borderBottom": "1px solid #f0f0f0", "paddingBottom": "4px"},
        children=[
            html.Span(label, className="has-text-grey is-size-7"),
            html.Span(id=field_id, className="has-text-weight-semibold is-size-7"),
        ],
    )


def make_table(df: pd.DataFrame, table_id: str, page_size: int = 10) -> dash_table.DataTable:
    if df is None or df.empty:
        return html.P("No data available.", className="has-text-grey is-size-7")

    return dash_table.DataTable(
        id=table_id,
        columns=[{"name": c.replace("_", " ").title(), "id": c} for c in df.columns],
        data=df.to_dict("records"),
        style_table={"overflowX": "auto", "fontSize": "0.78rem"},
        style_header={
            "backgroundColor": "#2c3e50",
            "color": "white",
            "fontWeight": "bold",
            "textAlign": "center",
            "padding": "6px 10px",
        },
        style_cell={
            "textAlign": "center",
            "padding": "5px 10px",
            "whiteSpace": "normal",
            "height": "auto",
        },
        style_data_conditional=[
            {"if": {"row_index": "odd"}, "backgroundColor": "#f5f7fa"},
            {
                "if": {"filter_query": '{status} = "ACTIVE"', "column_id": "status"},
                "color": "#257942",
                "fontWeight": "bold",
            },
        ],
        page_size=page_size,
        sort_action="native",
        filter_action="native",
    )


def empty_placeholder() -> html.P:
    return html.P("", className="has-text-grey is-size-7")


# ─── Layout ──────────────────────────────────────────────────────────────────

def layout():
    return html.Div(
        className="container",
        style={"overflow": "hidden"},
        children=[
            html.H1("Promotions Tracker", className="title has-text-centered mb-6"),

            # ── Section 1: Search Patron ──────────────────────────────────
            html.Div(
                className="box mb-5",
                children=[
                    html.H2("1. Search Patron (OM)", className="subtitle mb-4"),

                    html.Div(
                        className="field is-grouped mb-4",
                        children=[
                            html.Div(
                                className="control is-expanded",
                                children=[
                                    dcc.Input(
                                        id="pt-patron-search-input",
                                        type="text",
                                        placeholder="Enter OM Number (e.g. OM1)",
                                        className="input is-small",
                                        debounce=False,
                                    ),
                                ],
                            ),
                            html.Div(
                                className="control",
                                children=[
                                    html.Button(
                                        "Search",
                                        id="pt-patron-search-button",
                                        className="button is-info is-small",
                                        n_clicks=0,
                                    ),
                                ],
                            ),
                        ],
                    ),

                    html.Div(id="pt-patron-search-status", className="mb-3"),

                    # Patron details + offers — hidden until search
                    html.Div(
                        id="pt-patron-result-block",
                        style={"display": "none"},
                        children=[
                            html.Hr(style={"margin": "0.75rem 0"}),

                            # ── Patron Details ────────────────────────────
                            html.P(
                                "Patron Information",
                                className="has-text-info has-text-weight-semibold is-size-7 mb-2",
                                style={"textTransform": "uppercase", "letterSpacing": "0.05em"},
                            ),
                            html.Div(
                                className="columns is-variable is-4 mb-4",
                                children=[
                                    html.Div(className="column", children=[
                                        detail_field("OM Number",    "pt-detail-uid"),
                                        detail_field("Patron Name",  "pt-detail-name"),
                                    ]),
                                    html.Div(className="column", children=[
                                        detail_field("Tier",      "pt-detail-tier"),
                                        detail_field("Birthdate", "pt-detail-birthdate"),
                                    ]),
                                ],
                            ),

                            # ── Patron Offers Table ───────────────────────
                            html.P(
                                "Assigned Offers",
                                className="has-text-info has-text-weight-semibold is-size-7 mb-2",
                                style={"textTransform": "uppercase", "letterSpacing": "0.05em"},
                            ),
                            dcc.Loading(
                                html.Div(id="pt-offers-table-container", children=empty_placeholder()),
                            ),
                        ],
                    ),
                ],
            ),

            # ── Section 2: Active Promotions List ────────────────────────
            html.Div(
                className="box",
                children=[
                    html.H2("2. Search Active Promotion", className="subtitle mb-4"),

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
                                        "Search",
                                        id="pt-promo-search-button",
                                        className="button is-info is-small",
                                        n_clicks=0,
                                    ),
                                ],
                            ),
                        ],
                    ),

                    dcc.Loading(
                        html.Div(id="pt-promo-table-container"),
                    ),

                    html.P(
                        "Showing active promotions only.",
                        className="has-text-grey is-size-7 mt-3",
                    ),
                ],
            ),
        ],
    )


# ─── Callbacks ───────────────────────────────────────────────────────────────

@callback(
    Output("pt-detail-uid",            "children"),
    Output("pt-detail-name",           "children"),
    Output("pt-detail-tier",           "children"),
    Output("pt-detail-birthdate",      "children"),
    Output("pt-offers-table-container","children"),
    Output("pt-patron-search-status",  "children"),
    Output("pt-patron-result-block",   "style"),
    Input("pt-patron-search-button",   "n_clicks"),
    State("pt-patron-search-input",    "value"),
    prevent_initial_call=True,
)
def search_patron(n_clicks, om_input):
    hidden  = {"display": "none"}
    visible = {"display": "block"}
    blanks  = ("", "", "", "", empty_placeholder())

    if not om_input or not om_input.strip():
        msg = html.Span("Please enter an OM Number.", className="has-text-warning is-size-7")
        return (*blanks, msg, hidden)

    uid = om_input.strip().upper()

    # Look up patron details
    patron_row = DF_PATRONS[DF_PATRONS["uid"] == uid]
    if patron_row.empty:
        msg = html.Span(f"No patron found for '{uid}'.", className="has-text-danger is-size-7")
        return (*blanks, msg, hidden)

    p = patron_row.iloc[0]

    # Look up offers for this patron — drop uid column for display
    offers = DF_OFFERS[DF_OFFERS["uid"] == uid].drop(columns=["uid"])
    offers_table = make_table(offers, "pt-offers-table", page_size=5)

    msg = html.Span(f"Loaded patron: {uid}", className="has-text-success is-size-7")

    return (
        p["uid"],
        p["name"],
        p["tier"],
        p["birthdate"],
        offers_table,
        msg,
        visible,
    )


@callback(
    Output("pt-promo-table-container", "children"),
    Input("pt-promo-search-button",    "n_clicks"),
    Input("pt-promo-search-input",     "value"),
    prevent_initial_call=False,
)
def search_promos(n_clicks, query):
    df = DF_PROMOTIONS.copy()
    if query and query.strip():
        df = df[df["offer_name"].str.contains(query.strip(), case=False, na=False)]
    return make_table(df, "pt-promo-results-table")