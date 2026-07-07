import dash
from dash import Dash, dcc, html, callback, Input, Output, State, dash_table
import sys
import pandas as pd
import plotly.graph_objects as go
from utils.paths import PATRONDB


# Authentication Imports
from flask_login import current_user
from utils.login_handler import require_login, has_access, restricted_page

ROOT = "\\\\ominfstdpsd10001p-fs.int.okadamanila.com\\Casino\\Strategic Marketing\\Database Admin\\ETL\\Applications\\okada"
sys.path.append(ROOT)
from okada import LogService

logger = LogService("patron").get_logger()

ROOT = "\\\\ominfstdpsd10001p-fs.int.okadamanila.com\\Casino\\Strategic Marketing\\Database Admin\\ETL\\Applications"
sys.path.append(f"{ROOT}\\okada\\")
sys.path.append(f"{ROOT}\\reports\\pages\\")
from patron_etl.patron_etl import Patron


dash.register_page(__name__, path=PATRONDB)
require_login(
    __name__, access_level=restricted_page[PATRONDB]["access_level"])

# ─── Helpers ────────────────────────────────────────────────────────────────
def processuid(uid):
    """Normalize UID into format: OM######### (9 digits)."""
    if uid is None:
        return None
    digits = ''.join(filter(str.isdigit, str(uid)))

    if not digits:
        return None
    num = int(digits)
    if num > 999999999:
        return None

    return f"OM{num:09d}"

def make_chart(theo_df: pd.DataFrame, cwin_df: pd.DataFrame) -> dcc.Graph:
    if (theo_df is None or theo_df.empty) and (cwin_df is None or cwin_df.empty):
        return html.P("No visit data available.", className="has-text-grey is-size-7")

    fig = go.Figure()

    if theo_df is not None and not theo_df.empty:
        fig.add_trace(go.Scatter(
            name="Theo Win",
            x=theo_df["gamingdate"].astype(str),
            y=theo_df["theowin"],
            mode="lines+markers",
            line=dict(color="#3273dc"),
            hovertemplate="<b>%{x}</b><br>Theo Win: %{y}<extra></extra>",
        ))

    if cwin_df is not None and not cwin_df.empty:
        fig.add_trace(go.Scatter(
            name="Casino Win",
            x=cwin_df["gamingdate"].astype(str),
            y=cwin_df["casinowin"],
            mode="lines+markers",
            line=dict(color="#48c774"),
            hovertemplate="<b>%{x}</b><br>Casino Win: %{y}<extra></extra>",
        ))

    # ✅ Add zero reference line ONCE
    fig.add_hline(
        y=0,
        line=dict(color="red", width=2, dash="dash")
    )

    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="#f0f0f0"),
        height=220,
    )

    return dcc.Graph(figure=fig, config={"displayModeBar": False})


def make_table(df: pd.DataFrame, table_id: str) -> dash_table.DataTable:
    """Convert a DataFrame into a styled Dash DataTable."""
    if df is None or df.empty:
        return html.P("No data available.", className="has-text-grey is-size-7")

    return dash_table.DataTable(
        id=table_id,
        columns=[{"name": c, "id": c} for c in df.columns],
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
        ],
        page_size=10,
        sort_action="native",
    )


def detail_field(label: str, field_id: str) -> html.Div:
    """Cleaner patron detail row — label on left, value on right."""
    return html.Div(
        className="is-flex is-justify-content-space-between mb-2",
        style={"borderBottom": "1px solid #f0f0f0", "paddingBottom": "4px"},
        children=[
            html.Span(label, className="has-text-grey is-size-7"),
            html.Span(id=field_id, className="has-text-weight-semibold is-size-7"),
        ],
    )


def empty_table_placeholder(label: str) -> html.P:
    return html.P(f"", className="has-text-grey is-size-7")


# ─── Layout ─────────────────────────────────────────────────────────────────

def layout():
    # _layout()
    if current_user.is_authenticated and has_access(current_user, PATRONDB):
        logger.info(f"{current_user.id} has accessed")
        return _layout()
    else:
        return html.Div(["No Access!"])

def _layout():
    return html.Div(
        className="container",
        style={"overflow": "hidden"},
        children=[
            html.H1("Patron Dashboard", className="title has-text-centered mb-6"),

            # Main two-column container
            html.Div(
                className="columns",
                style={"overflowX": "hidden"},
                children=[

                    # ── Left column (1/3) ──────────────────────────────────
                    html.Div(
                        className="column is-one-third",
                        style={
                            "padding": "1rem",
                            "borderRight": "1px solid #ddd",
                            "boxSizing": "border-box",
                        },
                        children=[

                            # Search box
                            html.Div(
                                className="box mb-4",
                                children=[
                                    html.Label("Patron Search", className="label"),
                                    dcc.Input(
                                        id="patron-search-input",
                                        type="text",
                                        placeholder="Type patron id",
                                        className="input mb-2",
                                        debounce=False,
                                    ),
                                    html.Br(),
                                    html.Button(
                                        "Search",
                                        id="patron-search-button",
                                        className="button is-primary mt-2",
                                        n_clicks=0,
                                    ),
                                    html.Div(id="patron-search-status", className="mt-2"),
                                ],
                            ),

                            # Patron details box — DESIGN: replaced read-only inputs with cleaner label+value rows
                            html.Div(
                                className="box",
                                children=[
                                    html.H2("Patron Details", className="subtitle mb-3"),
                                    detail_field("Full Name",       "detail-fullname"),
                                    detail_field("Nationality",     "detail-nationality"),
                                    detail_field("Host",            "detail-host"),
                                    detail_field("Tier",            "detail-tier"),
                                    detail_field("Marketable",      "detail-marketable"),
                                    detail_field("Last Played",     "detail-last-played"),
                                    detail_field("Days Inactive",   "detail-days-inactive"),
                                    detail_field("Churn Risk",      "detail-churn-risk"),
                                    detail_field("Created Date",     "detail-created-date"),
                                    detail_field("Birth Date",     "detail-birthdate"),
                                ],
                            ),
                        ],
                    ),

                    # ── Right column (2/3) ─────────────────────────────────
                    # FIX: Cash, Rolling, Past 12 boxes were incorrectly nested
                    # inside the left column — moved here to the right column
                    html.Div(
                        className="column",
                        style={
                            "padding": "1rem",
                            "boxSizing": "border-box",
                        },
                        children=[

                            # Cash section
                            html.Div(
                                className="box mb-3",
                                children=[
                                    html.H2("Cash", className="subtitle mb-2"),
                                    html.Div(
                                        className="columns is-multiline is-variable is-2",
                                        children=[
                                            html.Div(className="column is-half", children=[
                                                html.P("ADT", className="has-text-weight-semibold is-size-7 mb-1"),
                                                html.Div(id="table-cash-adt", children=empty_table_placeholder("ADT")),
                                            ]),
                                            html.Div(className="column is-half", children=[
                                                html.P("Visits", className="has-text-weight-semibold is-size-7 mb-1"),
                                                html.Div(id="table-cash-visit", children=empty_table_placeholder("Visits")),
                                            ]),
                                            html.Div(className="column is-half", children=[
                                                html.P("Theoretical Win", className="has-text-weight-semibold is-size-7 mb-1"),
                                                html.Div(id="table-cash-twin", children=empty_table_placeholder("Theoretical Win")),
                                            ]),
                                            html.Div(className="column is-half", children=[
                                                html.P("Casino Win", className="has-text-weight-semibold is-size-7 mb-1"),
                                                html.Div(id="table-cash-cwin", children=empty_table_placeholder("Casino Win")),
                                            ]),
                                            html.Div(className="column is-full", children=[
                                                html.P("Theowin past 12 visit", className="has-text-weight-semibold is-size-7 mb-1"),
                                                html.Div(id="table-past12-theo", children=empty_table_placeholder("Theowin")),
                                            ]),
                                            # html.Div(className="column is-half", children=[
                                            #     html.P("Casino Win past 12 Visit", className="has-text-weight-semibold is-size-7 mb-1"),
                                            #     html.Div(id="table-past12-cwin", children=empty_table_placeholder("Casino Win")),
                                            # ]),
                                            html.Div(className="column is-full", children=[
                                                html.P("RI", className="has-text-weight-semibold is-size-7 mb-1"),
                                                html.Div(id="table-cash-ri", children=empty_table_placeholder("RI")),
                                            ]),
                                        ],
                                    ),
                                ],
                            ),

                            # Rolling section
                            html.Div(
                                className="box mb-3",
                                children=[
                                    html.H2("Rolling", className="subtitle mb-2"),
                                    html.Div(
                                        className="is-flex is-flex-direction-column",
                                        children=[
                                            html.Div(className="mb-3", children=[
                                                html.P("Rolling Summary", className="has-text-weight-semibold is-size-7 mb-1"),
                                                html.Div(id="table-rolling-main", children=empty_table_placeholder("Rolling")),
                                            ]),
                                            html.Div(className="mb-3", children=[
                                                html.P("Casino Win (PHP)", className="has-text-weight-semibold is-size-7 mb-1"),
                                                html.Div(id="table-rolling-cwinph", children=empty_table_placeholder("Casino Win PHP")),
                                            ]),
                                            html.Div(children=[
                                                html.P("Trip", className="has-text-weight-semibold is-size-7 mb-1"),
                                                html.Div(id="table-rolling-trip", children=empty_table_placeholder("Trip")),
                                            ]),
                                        ],
                                    ),
                                ],
                            ),

                            # Past 12 visits section — DESIGN: combined into one chart
                            # html.Div(
                            #     className="box",
                            #     children=[
                            #         html.H2("Past 12 Visits", className="subtitle mb-2"),
                            #         html.Div(
                            #             className="columns is-variable is-2",
                            #             children=[
                            #                 html.Div(className="column is-half", children=[
                            #                     html.P("Theoretical Win (last 12)", className="has-text-weight-semibold is-size-7 mb-1"),
                            #                     html.Div(id="table-past12-theo", children=empty_table_placeholder("Theo Win 12")),
                            #                 ]),
                            #                 html.Div(className="column is-half", children=[
                            #                     html.P("Casino Win (last 12)", className="has-text-weight-semibold is-size-7 mb-1"),
                            #                     html.Div(id="table-past12-cwin", children=empty_table_placeholder("Casino Win 12")),
                            #                 ]),
                            #             ],
                            #         ),
                            #     ],
                            # ),

                        ],
                    ),
                ],
            ),
        ],
    )


# ─── Callback ────────────────────────────────────────────────────────────────

@callback(
    Output("detail-fullname",       "children"),   # FIX: was "value" (Input), now "children" (Span)
    Output("detail-nationality",    "children"),
    Output("detail-host",           "children"),
    Output("detail-tier",           "children"),
    Output("detail-marketable",     "children"),
    Output("detail-last-played",    "children"),
    Output("detail-days-inactive",  "children"),
    Output("detail-churn-risk",     "children"),
    Output("detail-created-date",   "children"),
    Output("detail-birthdate",   "children"),
    Output("table-past12-theo",     "children"),
    # Output("table-past12-cwin",     "children"),
    Output("table-cash-adt",        "children"),
    Output("table-cash-visit",      "children"),
    Output("table-cash-ri",         "children"),
    Output("table-cash-twin",       "children"),
    Output("table-cash-cwin",       "children"),
    Output("table-rolling-main",    "children"),
    Output("table-rolling-cwinph",  "children"),
    Output("table-rolling-trip",    "children"),
    Output("patron-search-status",  "children"),
    Input("patron-search-button",   "n_clicks"),
    State("patron-search-input",    "value"),
    prevent_initial_call=True,
)
def search_click(n_clicks, universalplayerid):
    if not universalplayerid or not universalplayerid.strip():
        blanks = [""] * 8
        placeholders = [empty_table_placeholder("")] * 10
        msg = html.Span("Please enter a Patron ID.", className="has-text-warning is-size-7")
        return (*blanks, *placeholders, msg)

    try:
        puid = processuid(universalplayerid)
        patroninfo = Patron()
        patroninfo.set_patron(puid.strip())
        yesterday= pd.Timestamp.today().normalize() - pd.Timedelta(days=1)
        patroninfo.set_reference(yesterday.strftime('%Y-%m-%d'))
        # patroninfo.set_reference("2026-04-14")

        fullname, nationality, host, tier, marketable, last_played, days_inactive, churn_risk, created_date, birthday = patroninfo.get_patron_details()
        # theo12, cwin12 = patroninfo.get_last12visit()
        adt_df, visit_df, ri_df, twin_df, cwin_df, theo12 = patroninfo.get_cash()
        rolling_df, cwinph_df, trip_df = patroninfo.get_rolling()

        # past12_chart_theo  = make_chart(theo12, None)
        # past12_chart_cwin  = make_chart(None, cwin12)
        past12_chart_theo  = None
        past12_chart_cwin  =None

        status = html.Span(f"Loaded patron: {puid}", className="has-text-success is-size-7")

        return (
            str(fullname      or ""),
            str(nationality   or ""),
            str(host          or ""),
            str(tier          or ""),
            str(marketable    or ""),
            str(last_played   or ""),
            str(days_inactive or ""),
            # str(churn_risk    or ""),
            "",#churn
            str(created_date   or ""),
            str(pd.to_datetime(birthday).strftime('%B %d, %Y') if birthday else ""),
            make_table(theo12,      "dt-cash-theo12"),
            # make_table(None,      "dt-cash-cwin12"),
            make_table(adt_df,      "dt-cash-adt"),
            make_table(visit_df,    "dt-cash-visit"),
            make_table(ri_df,       "dt-cash-ri"),
            make_table(twin_df,     "dt-cash-twin"),
            make_table(cwin_df,     "dt-cash-cwin"),
            make_table(rolling_df,  "dt-rolling-main"),
            make_table(cwinph_df,   "dt-rolling-cwinph"),
            make_table(trip_df,     "dt-rolling-trip"),
            status,
        )

    except Exception as e:
        error_msg = html.Span(f"Error: {str(e)}", className="has-text-danger is-size-7")
        blanks = [""] * 8
        placeholders = [html.P("Error loading data.", className="has-text-danger is-size-7")] * 10
        return (*blanks, *placeholders, error_msg)
