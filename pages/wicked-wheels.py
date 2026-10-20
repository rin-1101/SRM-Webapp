import json
import logging
import runpy
from datetime import datetime, timedelta, timezone
from io import StringIO
from pathlib import Path

import dash
import pandas as pd
from dash import Input, Output, State, callback, dash_table, dcc, html
from dash.exceptions import PreventUpdate
from flask_login import current_user

from utils.login_handler import has_access, require_login, restricted_page
from utils.paths import WICKED_WHEELS


logger = logging.getLogger("wicked-wheels")
REFERENCE_PATH = Path(__file__).resolve().parents[1] / "reference" / "dis-qualified.py"
MANILA = timezone(timedelta(hours=8))
REPORT_COLUMNS = [
    "UniversalPlayerID", "TierName", "Coding", "TP",
]
DISPLAY_COLUMNS = ["UniversalPlayerID", "TP"]

dash.register_page(__name__, path=WICKED_WHEELS, name="Wicked Wheels")
require_login(__name__, access_level=restricted_page[WICKED_WHEELS]["access_level"])


def layout():
    if not has_access(current_user, WICKED_WHEELS):
        return html.Div("No Access!")
    return html.Div(
        className="container mt-5",
        children=[
            html.H1("Wicked Wheels", className="title has-text-centered"),
            html.Div(className="box", children=[
                html.P("Generate today's Wicked Wheels report, from 6:00 AM to before 10:00 AM (Manila time). Displays patrons with TP >= 1."),
                html.Div(className="buttons mt-3", children=[
                    html.Button("Generate", id="wicked-wheels-generate",
                                n_clicks=0, className="button is-info"),
                    html.Button("Export Excel", id="wicked-wheels-export",
                                n_clicks=0, disabled=True, className="button is-primary"),
                ]),
            ]),
            dcc.Store(id="wicked-wheels-report", storage_type="memory"),
            dcc.Download(id="wicked-wheels-download"),
            dcc.Loading(children=[
                html.Div(id="wicked-wheels-status", className="mb-3"),
                dash_table.DataTable(
                    id="wicked-wheels-table", data=[],
                    columns=[{"name": column, "id": column} for column in DISPLAY_COLUMNS],
                    page_size=20, sort_action="native", filter_action="native",
                    style_table={"overflowX": "auto"},
                    style_header={"backgroundColor": "#2c3e50", "color": "white",
                                  "fontWeight": "bold"},
                    style_cell={"padding": "8px", "textAlign": "left",
                                "whiteSpace": "normal", "height": "auto"},
                ),
            ]),
            html.Div(id="wicked-wheels-export-status", className="mt-3"),
        ],
    )


@callback(
    Output("wicked-wheels-table", "data"),
    Output("wicked-wheels-table", "columns"),
    Output("wicked-wheels-report", "data"),
    Output("wicked-wheels-status", "children"),
    Output("wicked-wheels-export", "disabled"),
    Input("wicked-wheels-generate", "n_clicks"),
    prevent_initial_call=True,
    running=[(Output("wicked-wheels-generate", "disabled"), True, False)],
)
def generate_report(n_clicks):
    if not n_clicks:
        raise PreventUpdate
    columns = [{"name": column, "id": column} for column in DISPLAY_COLUMNS]
    if not has_access(current_user, WICKED_WHEELS):
        return [], columns, None, html.P("No Access!", className="has-text-danger"), True
    try:
        reference = runpy.run_path(str(REFERENCE_PATH))
        generated_at = datetime.now(MANILA)
        start, end = reference["report_window"](generated_at)
        result = reference["generate_report"](now=generated_at)
        if result.empty:
            result = result.reindex(columns=REPORT_COLUMNS)
        snapshot = {
            "json": result.to_json(orient="split", date_format="iso", double_precision=15),
            "date_columns": list(result.select_dtypes(include=["datetime", "datetimetz"]).columns),
            "generated_at": generated_at.isoformat(),
        }
        display = result.loc[pd.to_numeric(result["TP"], errors="coerce").ge(1), DISPLAY_COLUMNS]
        records = json.loads(display.to_json(orient="records", double_precision=15))
    except Exception:
        logger.exception("Wicked Wheels report generation failed")
        return [], columns, None, html.P(
            "Unable to generate the report. Please try again.", className="has-text-danger"
        ), True
    message = (
        f"{len(records):,} rows with TP >= 1. Report period: {start:%Y-%m-%d %I:%M %p} "
        f"to before {end:%Y-%m-%d %I:%M %p} (Manila time)."
    )
    if not records:
        message = "No results found. " + message
    return records, columns, snapshot, html.P(message, className="notification is-info"), False


@callback(
    Output("wicked-wheels-download", "data"),
    Output("wicked-wheels-export-status", "children"),
    Input("wicked-wheels-export", "n_clicks"),
    State("wicked-wheels-report", "data"),
    prevent_initial_call=True,
)
def export_report(n_clicks, snapshot):
    if not n_clicks or not snapshot:
        raise PreventUpdate
    if not has_access(current_user, WICKED_WHEELS):
        return dash.no_update, html.P("No Access!", className="has-text-danger")
    try:
        result = pd.read_json(
            StringIO(snapshot["json"]), orient="split", dtype=False,
            convert_dates=False,
        )
        for column in snapshot["date_columns"]:
            result[column] = pd.to_datetime(result[column])
            if isinstance(result[column].dtype, pd.DatetimeTZDtype):
                result[column] = result[column].dt.tz_convert(MANILA).dt.tz_localize(None)
        generated_at = datetime.fromisoformat(snapshot["generated_at"])
        download = dcc.send_data_frame(
            result.to_excel, f"wicked_wheels_{generated_at:%Y-%m-%d_%H%M%S}.xlsx",
            sheet_name="Wicked Wheels", index=False, engine="openpyxl",
        )
    except Exception:
        logger.exception("Wicked Wheels Excel export failed")
        return dash.no_update, html.P(
            "Unable to export the report. Please try again.", className="has-text-danger"
        )
    return download, ""
