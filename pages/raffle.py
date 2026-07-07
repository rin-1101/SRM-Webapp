import dash
import random
import pandas as pd
from dash import Dash, dcc, html, dash_table, Input, Output, State, callback, ctx

dash.register_page(__name__, path="/raffle")



def layout():
    return html.Div(
        [
            html.H1("Raffle:", className="title"),
            html.Div(
                style={"display": "flex", "justify-content": "center", "padding": "20px 0"},
                children=[
                    html.Div(
                        id="raffle-form",
                        className="box",
                        style={"width": "30%", "border-radius": "10px", "box-shadow": "5px 5px 5px grey"},
                        children=[
                            html.Div(
                                className="field",
                                children=[
                                    html.Label("Participants1", className="label"),
                                    dcc.Input(type="number", id="raffle_participants", required=True, className="input"),
                                ],
                            ),
                            html.Div(
                                className="field",
                                children=[
                                    html.Label("Winners", className="label"),
                                    dcc.Input(type="number", id="raffle_winners", required=True, className="input"),
                                ],
                            ),
                            html.Div(
                                className="field is-grouped",
                                children=[
                                    html.Div(
                                        className="control",
                                        children=[
                                            html.Button("Submit", id="submit-button_raffle", type="submit", className="button is-info", n_clicks=0),
                                            html.Button("Download CSV", id="download-button_raffle", className="button is-success", n_clicks=0),
                                        ],
                                    )
                                ],
                            ),
                        ],
                    )
                ],
            ),
            dcc.Loading(html.Div(id="output-data_raffle")),
            dcc.Download(id="download-data_raffle"),
        ]
    )

@callback(
    Output("output-data_raffle", "children"),
    Output("download-data_raffle", "data"),
    Input("submit-button_raffle", "n_clicks"),
    Input("download-button_raffle", "n_clicks"),
    State("raffle_participants", "value"),
    State("raffle_winners", "value"),
    prevent_initial_call=True,
)
def run_raffle(submit_n, download_n, participants, winners):
    trigger_id = ctx.triggered_id
    if not participants or not winners or winners > participants:
        return "Invalid input. Ensure participants > winners.", None

    winner_list = random.sample(range(1, participants + 1), winners)
    df = pd.DataFrame({"Winner #": range(1, winners + 1), "Participant ID": winner_list})

    if trigger_id == "submit-button_raffle":
        return dash_table.DataTable(df.to_dict("records"), [{"name": i, "id": i} for i in df.columns]), None
    elif trigger_id == "download-button_raffle":
        return None, dcc.send_data_frame(df.to_csv, "raffle_winners.csv", index=False)

    return None, None
