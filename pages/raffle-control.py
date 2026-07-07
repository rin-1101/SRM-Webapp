import dash
from dash import html, dcc, callback, Input, Output, State
from dash import callback_context as context
from dash.exceptions import PreventUpdate

import pandas as pd
import time
import sys
import yaml

from pathlib import Path
from datetime import datetime

ROOT = "\\\\ominfstdpsd10001p-fs.int.okadamanila.com\\Casino\\Strategic Marketing\\Database Admin\\ETL\\Applications"

sys.path.append(f"{ROOT}\\okada\\")
sys.path.append(f"{ROOT}\\reports\\pages\\")

from raffle_etl.raffle import Raffle_app
from raffle_etl.shareddata import get_data, save_data
from raffle_etl.rafflecontrol import RaffleControl

raffle = Raffle_app()
controller = RaffleControl()

dash.register_page(__name__, path='/backend')

BASE_DIR = Path(__file__).parent.parent

def layout():

    default_event = controller.get_default_event()

    data = get_data(default_event)

    return html.Div([

        html.Div(className="container", children=[

            html.Div(className="section", children=[

                html.H1(
                    className="title is-2",
                    children="Backend Control Panel"
                ),

                html.Div(
                    className="box",
                    children=[

                        html.H2(
                            className="title is-4",
                            children="Promotion"
                        ),

                        dcc.Dropdown(
                            id="raffle-dropdown",
                            options=controller.get_dropdown_options(),
                            value=default_event
                        ),
                    ],
                ),

                html.Div(
                    className="box",
                    children=[

                        html.H2(
                            className="title is-4",
                            children="Raffle Draw"
                        ),

                        html.Button(
                            id='raffle-button',
                            className="button is-primary is-large mt-4",
                            children="🎲 Draw Raffle",
                            n_clicks=0
                        ),

                        html.Button(
                            id='reset-button',
                            className="button is-warning is-large mt-4 ml-2",
                            children="Reset",
                            n_clicks=0
                        ),

                        html.Button(
                            id='next-button',
                            className="button is-info is-large mt-4 ml-2",
                            children="Next Draw",
                            n_clicks=0
                        ),

                        html.Div(
                            id='raffle-result',
                            className="notification mt-4",
                            style={'display': 'none'}
                        )
                    ]
                ),

                html.Div(
                    className="box mt-5",
                    children=[

                        html.H2(
                            className="title is-4",
                            children="Set Time and Date"
                        ),

                        html.Div(
                            className="field",
                            children=[

                                html.Label(
                                    className="label",
                                    children="Time"
                                ),

                                html.Div(
                                    className="control",
                                    children=[

                                        dcc.Dropdown(
                                            id='time-input',
                                            options=[],
                                            value=data['time'],
                                            className="input"
                                        )
                                    ]
                                )
                            ]
                        ),

                        html.Div(
                            className="field",
                            children=[

                                html.Label(
                                    className="label",
                                    children="Date"
                                ),

                                html.Div(
                                    className="control",
                                    children=[

                                        dcc.Dropdown(
                                            id='date-input',
                                            options=[],
                                            value=data['date'],
                                            className="input"
                                        )
                                    ]
                                )
                            ]
                        ),

                        html.Div(
                            className="field",
                            children=[

                                html.Label(
                                    className="label",
                                    children="Prize"
                                ),

                                html.Div(
                                    className="control",
                                    children=[

                                        dcc.Dropdown(
                                            id='prize-input',
                                            options=[],
                                            value=data['prize'],
                                            className="input"
                                        )
                                    ]
                                )
                            ]
                        ),

                        html.Button(
                            id='apply-button',
                            className="button is-success is-large mt-4",
                            children="✓ Apply Changes",
                            n_clicks=0
                        ),

                        html.Div(
                            id='apply-status',
                            className="notification mt-4",
                            style={'display': 'none'}
                        )
                    ]
                ),

                html.Div(
                    className="box mt-5",
                    children=[

                        html.H2(
                            className="title is-4",
                            children="Current Frontend Values"
                        ),

                        dcc.Interval(
                            id='backend-interval',
                            interval=1000,
                            n_intervals=0
                        ),

                        html.Div(
                            id='current-values',
                            className="content"
                        )
                    ]
                )
            ])
        ]),

        dcc.Store(id='csv-data-store')
    ])


@callback(
    [
        Output('raffle-result', 'children'),
        Output('raffle-result', 'style'),
        Output('raffle-result', 'className')
    ],
    Input('raffle-button', 'n_clicks'),
    Input('reset-button', 'n_clicks'),
    Input('next-button', 'n_clicks'),
    State('raffle-dropdown', 'value'),
    prevent_initial_call=True
)
def draw_raffle(
    raffle_clicks,
    reset_clicks,
    next_clicks,
    event_name
):

    current_data = get_data(event_name)

    ctx = context.triggered

    if not ctx:
        raise PreventUpdate

    trigger_id = ctx[0]['prop_id'].split('.')[0]

    if trigger_id == 'reset-button':

        current_data['uid'] = controller.get_message(
            event_name,
            "reset"
        )

        current_data['initials'] = "-"

        current_data['animation_timestamp'] = time.time()

        save_data(current_data, event_name)

        return (
            "🎉 Reset Successful",
            {'display': 'block'},
            "notification is-success"
        )

    if trigger_id == 'next-button':

        current_data['uid'] = controller.get_message(
            event_name,
            "next_draw"
        )

        current_data['initials'] = "-"

        current_data['animation_timestamp'] = time.time()

        save_data(current_data, event_name)

        return (
            "🎉 Next Draw Updated",
            {'display': 'block'},
            "notification is-info"
        )

    uid, initials = raffle.draw(event_name)

    current_data['uid'] = uid
    current_data['initials'] = initials
    current_data['animation_timestamp'] = time.time()

    save_data(current_data, event_name)

    current_hour = datetime.now().hour

    if current_hour == 21:
        is_redraw = False

    elif current_hour == 22:
        is_redraw = True

    else:
        is_redraw = f"Drawn at {current_hour}"

    result_data = pd.DataFrame({
        "uid": [uid],
        "initials": [initials],
        "time": [datetime.now()],
        "redraw": [is_redraw]
    })

    raffle.write_draw(result_data)

    msg = f"🎉 Winner drawn! UID: {uid}, Initials: {initials}"

    return (
        msg,
        {'display': 'block'},
        "notification is-success"
    )


@callback(
    [
        Output(
            'apply-status',
            'children',
            allow_duplicate=True
        ),

        Output('apply-status', 'style'),

        Output('apply-status', 'className')
    ],
    Input('apply-button', 'n_clicks'),
    State('raffle-dropdown', 'value'),
    State('time-input', 'value'),
    State('date-input', 'value'),
    State('prize-input', 'value'),
    prevent_initial_call='initial_duplicate'
)
def apply_changes(
    n_clicks,
    event_name,
    time_val,
    date_val,
    prize
):

    if not n_clicks:
        raise PreventUpdate

    if not time_val or not date_val or not prize:

        return (
            "❌ Missing required fields!",
            {'display': 'block'},
            "notification is-danger"
        )

    current_data = get_data(event_name)

    current_data['time'] = time_val
    current_data['date'] = date_val
    current_data['prize'] = prize

    save_data(current_data, event_name)

    return (
        f"✓ Changes applied successfully!",
        {'display': 'block'},
        "notification is-success"
    )


@callback(
    Output(
        'current-values',
        'children',
        allow_duplicate=True
    ),
    Input('backend-interval', 'n_intervals'),
    State('raffle-dropdown', 'value'),
    prevent_initial_call='initial_duplicate'
)
def show_current_values(n, event_name):

    data = get_data(event_name)

    return html.Div([

        html.P([
            html.Strong("UID: "),
            data['uid']
        ]),

        html.P([
            html.Strong("Initials: "),
            data['initials']
        ]),

        html.P([
            html.Strong("Time: "),
            data['time']
        ]),

        html.P([
            html.Strong("Date: "),
            data['date']
        ]),

        html.P([
            html.Strong("Prize: "),
            data['prize']
        ]),
    ])


@callback(
    Output('time-input', 'options'),
    Input('raffle-dropdown', 'value'),
)
def set_time(event_name):

    if not event_name:
        return []

    return controller.get_time_options(event_name)


@callback(
    Output('date-input', 'options'),
    Input('raffle-dropdown', 'value'),
)
def set_date(event_name):

    if not event_name:
        return []

    return controller.get_date_options(event_name)


@callback(
    Output('prize-input', 'options'),
    Input('raffle-dropdown', 'value'),
)
def set_prize(event_name):

    if not event_name:
        return []

    return controller.get_prize_options(event_name)


@callback(
    Output('date-input', 'value'),
    Output('time-input', 'value'),
    Output('prize-input', 'value'),
    Input('raffle-dropdown', 'value'),
    prevent_initial_call='initial_duplicate'
)
def set_dropdown_values(event_name):

    event_data = get_data(event_name)

    return (
        event_data['date'],
        event_data['time'],
        event_data['prize']
    )