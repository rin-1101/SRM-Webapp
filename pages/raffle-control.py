import time
from datetime import datetime

import dash
import pandas as pd
from dash import Input, Output, State, callback, callback_context, dash_table, dcc, html
from dash.exceptions import PreventUpdate

from templates.raffle import RaffleApp, RaffleControl, get_data, save_data


raffle = RaffleApp()
controller = RaffleControl()

dash.register_page(__name__, path="/backend")


def _winner_rows(event_name):
    winners = raffle.get_current_set_winners(event_name).rename(
        columns={
            "UniversalPlayerID": "uid",
            "Name": "name",
            "won_entries": "wins",
            "remaining_entries": "remaining",
        }
    )
    return winners.to_dict("records")


def layout():
    default_event = controller.get_default_event()
    data = get_data(default_event)

    draw_box = html.Div(
        className="box",
        children=[
            html.H2("Raffle Draw", className="title is-4"),
            html.Div(
                className="buttons",
                children=[
                    html.Button(
                        "Draw Raffle",
                        id="raffle-button",
                        className="button is-primary is-large",
                        n_clicks=0,
                    ),
                    html.Button(
                        "New Winner Set",
                        id="new-set-button",
                        className="button is-success is-large",
                        n_clicks=0,
                    ),
                    html.Button(
                        "Reset Screen",
                        id="reset-button",
                        className="button is-warning is-large",
                        n_clicks=0,
                    ),
                    html.Button(
                        "Next Draw",
                        id="next-button",
                        className="button is-info is-large",
                        n_clicks=0,
                    ),
                ],
            ),
            html.Div(
                id="raffle-result",
                className="notification mt-4",
                style={"display": "none"},
            ),
        ],
    )

    reset_list_box = html.Div(
        className="box",
        children=[
            html.H2("Reset List", className="title is-4"),
            html.P(
                "Restore all used entries and clear the current winner set.",
                className="content",
            ),
            html.Button(
                "Reset List",
                id="reset-list-button",
                className="button is-danger",
                n_clicks=0,
            ),
            html.Div(
                id="reset-list-status",
                className="notification mt-4",
                style={"display": "none"},
            ),
        ],
    )

    settings_box = html.Div(
        className="box",
        children=[
            html.H2("Draw Details", className="title is-4"),
            html.Div(
                className="field",
                children=[
                    html.Label("Time", className="label"),
                    dcc.Dropdown(
                        id="time-input",
                        options=[],
                        value=data["time"],
                        className="input",
                    ),
                ],
            ),
            html.Div(
                className="field",
                children=[
                    html.Label("Date", className="label"),
                    dcc.Dropdown(
                        id="date-input",
                        options=[],
                        value=data["date"],
                        className="input",
                    ),
                ],
            ),
            html.Div(
                className="field",
                children=[
                    html.Label("Prize", className="label"),
                    dcc.Dropdown(
                        id="prize-input",
                        options=[],
                        value=data["prize"],
                        className="input",
                    ),
                ],
            ),
            html.Button(
                "Apply Changes",
                id="apply-button",
                className="button is-success",
                n_clicks=0,
            ),
            html.Div(
                id="apply-status",
                className="notification mt-4",
                style={"display": "none"},
            ),
        ],
    )

    winners_box = html.Div(
        className="box",
        children=[
            html.Div(
                className="is-flex is-justify-content-space-between is-align-items-center mb-3",
                children=[
                    html.H2("Current Winner Set", className="title is-4 mb-0"),
                    html.Div(
                        className="buttons mb-0",
                        children=[
                            html.Button(
                                "Refresh",
                                id="refresh-winners-button",
                                className="button is-light",
                                n_clicks=0,
                            ),
                            html.Button(
                                "Export CSV",
                                id="export-winners-button",
                                className="button is-link is-light",
                                n_clicks=0,
                            ),
                        ],
                    ),
                ],
            ),
            dcc.Download(id="winners-csv-download"),
            html.Div(id="entry-summary", className="content mb-3"),
            dash_table.DataTable(
                id="previous-winners-table",
                columns=[
                    {"name": "Draw #", "id": "draw_number", "type": "numeric"},
                    {"name": "UID", "id": "uid"},
                    {"name": "Name", "id": "name"},
                    {"name": "Entries Used", "id": "wins", "type": "numeric"},
                    {"name": "Entries Left", "id": "remaining", "type": "numeric"},
                ],
                data=_winner_rows(default_event),
                page_size=5,
                sort_action="native",
                style_table={"overflowX": "auto"},
                style_cell={
                    "padding": "0.65rem",
                    "textAlign": "left",
                    "whiteSpace": "nowrap",
                },
                style_header={"fontWeight": "bold"},
            ),
        ],
    )

    current_box = html.Div(
        className="box",
        children=[
            html.H2("Current Frontend Values", className="title is-4"),
            dcc.Interval(id="backend-interval", interval=1000, n_intervals=0),
            html.Div(id="current-values", className="content"),
        ],
    )

    return html.Div(
        className="container",
        style={"maxWidth": "1200px", "padding": "1.5rem"},
        children=[
            html.H1("Raffle Control", className="title is-2"),
            html.Div(
                className="box",
                children=[
                    html.Label("Promotion", className="label"),
                    dcc.Dropdown(
                        id="raffle-dropdown",
                        options=controller.get_dropdown_options(),
                        value=default_event,
                        clearable=False,
                    ),
                ],
            ),
            html.Div(
                className="columns is-variable is-5",
                children=[
                    html.Div(
                        className="column is-5",
                        children=[draw_box, reset_list_box, settings_box],
                    ),
                    html.Div(
                        className="column is-7",
                        children=[winners_box, current_box],
                    ),
                ],
            ),
        ],
    )


@callback(
    Output("raffle-result", "children"),
    Output("raffle-result", "style"),
    Output("raffle-result", "className"),
    Input("raffle-button", "n_clicks"),
    Input("new-set-button", "n_clicks"),
    Input("reset-button", "n_clicks"),
    Input("next-button", "n_clicks"),
    State("raffle-dropdown", "value"),
    prevent_initial_call=True,
)
def draw_raffle(raffle_clicks, new_set_clicks, reset_clicks, next_clicks, event_name):
    if not callback_context.triggered:
        raise PreventUpdate

    trigger_id = callback_context.triggered[0]["prop_id"].split(".")[0]
    current_data = get_data(event_name)

    if trigger_id == "new-set-button":
        raffle.start_new_set(event_name)
        current_data["uid"] = "New Winner Set"
        current_data["initials"] = "-"
        current_data["animation_timestamp"] = 0
        save_data(current_data, event_name)
        return (
            "New winner set started. Consumed entries were kept.",
            {"display": "block"},
            "notification is-success",
        )
    if trigger_id == "reset-button":
        current_data["uid"] = controller.get_message(event_name, "reset")
        current_data["initials"] = "-"
        current_data["animation_timestamp"] = time.time()
        save_data(current_data, event_name)
        return (
            "Screen reset. Consumed entries were kept.",
            {"display": "block"},
            "notification is-success",
        )

    if trigger_id == "next-button":
        current_data["uid"] = controller.get_message(event_name, "next_draw")
        current_data["initials"] = "-"
        current_data["animation_timestamp"] = time.time()
        save_data(current_data, event_name)
        return (
            "Next draw screen is ready.",
            {"display": "block"},
            "notification is-info",
        )

    try:
        uid, initials = raffle.draw(event_name)
    except (FileNotFoundError, ValueError) as error:
        return (
            str(error),
            {"display": "block"},
            "notification is-danger",
        )

    if uid is None:
        current_data["uid"] = "No Winners"
        current_data["initials"] = "-"
        current_data["animation_timestamp"] = 0
        save_data(current_data, event_name)
        return (
            "No unique winners remain. Start a new winner set to draw again.",
            {"display": "block"},
            "notification is-warning",
        )

    current_data["uid"] = uid
    current_data["initials"] = initials
    current_data["animation_timestamp"] = time.time()
    save_data(current_data, event_name)

    current_hour = datetime.now().hour
    if current_hour == 21:
        is_redraw = False
    elif current_hour == 22:
        is_redraw = True
    else:
        is_redraw = f"Drawn at {current_hour}"

    result_data = pd.DataFrame({
        "event": [event_name],
        "uid": [uid],
        "initials": [initials],
        "time": [datetime.now()],
        "redraw": [is_redraw],
    })
    raffle.write_draw(result_data)

    return (
        f"Winner drawn: {uid} - {initials}",
        {"display": "block"},
        "notification is-success",
    )


@callback(
    Output("reset-list-status", "children"),
    Output("reset-list-status", "style"),
    Output("reset-list-status", "className"),
    Input("reset-list-button", "n_clicks"),
    State("raffle-dropdown", "value"),
    prevent_initial_call=True,
)
def reset_list(n_clicks, event_name):
    if not n_clicks:
        raise PreventUpdate

    try:
        summary = raffle.reset_entries(event_name)
    except (FileNotFoundError, ValueError) as error:
        return (
            str(error),
            {"display": "block"},
            "notification is-danger",
        )

    current_data = get_data(event_name)
    current_data["uid"] = controller.get_message(event_name, "reset")
    current_data["initials"] = "-"
    current_data["animation_timestamp"] = 0
    save_data(current_data, event_name)

    return (
        f"List reset: {summary['total']:,} entries, 0 used, "
        f"{summary['remaining']:,} remaining.",
        {"display": "block"},
        "notification is-success",
    )


@callback(
    Output("previous-winners-table", "data"),
    Output("entry-summary", "children"),
    Input("refresh-winners-button", "n_clicks"),
    Input("raffle-dropdown", "value"),
    Input("raffle-result", "children"),
    Input("reset-list-status", "children"),
)
def refresh_previous_winners(
    refresh_clicks,
    event_name,
    raffle_result,
    reset_list_status,
):
    if not event_name:
        return [], ""

    try:
        rows = _winner_rows(event_name)
        summary = raffle.get_entry_summary(event_name)
    except (FileNotFoundError, ValueError) as error:
        return [], str(error)

    return rows, (
        f"{summary['set_winners']:,} unique winners in this set / "
        f"{summary['used']:,} entries used / "
        f"{summary['remaining']:,} entries remaining"
    )


@callback(
    Output("winners-csv-download", "data"),
    Input("export-winners-button", "n_clicks"),
    State("raffle-dropdown", "value"),
    prevent_initial_call=True,
)
def export_winners(n_clicks, event_name):
    if not n_clicks or not event_name:
        raise PreventUpdate

    winners = raffle.get_current_set_winners(event_name).rename(
        columns={
            "draw_number": "Draw #",
            "UniversalPlayerID": "UID",
            "Name": "Name",
            "won_entries": "Entries Used",
            "remaining_entries": "Entries Left",
            "drawn_at": "Drawn At",
        }
    )
    export_columns = [
        "Draw #",
        "UID",
        "Name",
        "Entries Used",
        "Entries Left",
        "Drawn At",
    ]
    winners = winners.reindex(columns=export_columns)
    filename_event = "".join(
        character if character.isalnum() or character in ("-", "_") else "_"
        for character in event_name
    ).strip("_")
    filename = f"{filename_event or 'raffle'}_winners.csv"
    return dcc.send_data_frame(winners.to_csv, filename, index=False)


@callback(
    Output("apply-status", "children"),
    Output("apply-status", "style"),
    Output("apply-status", "className"),
    Input("apply-button", "n_clicks"),
    State("raffle-dropdown", "value"),
    State("time-input", "value"),
    State("date-input", "value"),
    State("prize-input", "value"),
    prevent_initial_call=True,
)
def apply_changes(n_clicks, event_name, time_value, date_value, prize):
    if not n_clicks:
        raise PreventUpdate
    if not time_value or not date_value or prize in (None, ""):
        return (
            "Complete all draw details.",
            {"display": "block"},
            "notification is-danger",
        )

    current_data = get_data(event_name)
    current_data.update({"time": time_value, "date": date_value, "prize": prize})
    save_data(current_data, event_name)
    return (
        "Changes applied.",
        {"display": "block"},
        "notification is-success",
    )


@callback(
    Output("current-values", "children"),
    Input("backend-interval", "n_intervals"),
    State("raffle-dropdown", "value"),
)
def show_current_values(n_intervals, event_name):
    data = get_data(event_name)
    return html.Div([
        html.P([html.Strong("UID: "), data.get("uid", "-")]),
        html.P([html.Strong("Initials: "), data.get("initials", "-")]),
        html.P([html.Strong("Time: "), data.get("time", "-")]),
        html.P([html.Strong("Date: "), data.get("date", "-")]),
        html.P([html.Strong("Prize: "), str(data.get("prize", "-"))]),
    ])


@callback(Output("time-input", "options"), Input("raffle-dropdown", "value"))
def set_time(event_name):
    return controller.get_time_options(event_name) if event_name else []


@callback(Output("date-input", "options"), Input("raffle-dropdown", "value"))
def set_date(event_name):
    return controller.get_date_options(event_name) if event_name else []


@callback(Output("prize-input", "options"), Input("raffle-dropdown", "value"))
def set_prize(event_name):
    return controller.get_prize_options(event_name) if event_name else []


@callback(
    Output("date-input", "value"),
    Output("time-input", "value"),
    Output("prize-input", "value"),
    Input("raffle-dropdown", "value"),
)
def set_dropdown_values(event_name):
    event_data = get_data(event_name)
    return event_data["date"], event_data["time"], event_data["prize"]
