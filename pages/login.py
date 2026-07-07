import dash
from dash import html, dcc


dash.register_page(__name__, path="/login")


def layout():
    return html.Div(
        [
            html.Section(
                className="section",
                children=[
                    html.Div(
                        className="container",
                        children=[
                            html.Div(
                                className="columns is-centered",
                                children=[
                                    html.Div(
                                        className="column is-half",
                                        children=[
                                            html.Div(
                                                className="box",
                                                children=[
                                                    html.H1(
                                                        className="title",
                                                        children="Login",
                                                    ),
                                                    html.Form(
                                                        children=[
                                                            html.Div(
                                                                className="field",
                                                                children=[
                                                                    html.Label(
                                                                        className="label",
                                                                        children="Username",
                                                                    ),
                                                                    html.Div(
                                                                        className="control",
                                                                        children=[
                                                                            dcc.Input(
                                                                                className="input",
                                                                                type="text",
                                                                                placeholder="Enter your username",
                                                                                id="uname-box",
                                                                                name="username",
                                                                            )
                                                                        ],
                                                                    ),
                                                                ],
                                                            ),
                                                            html.Div(
                                                                className="field",
                                                                children=[
                                                                    html.Label(
                                                                        className="label",
                                                                        children="Password",
                                                                    ),
                                                                    html.Div(
                                                                        className="control",
                                                                        children=[
                                                                            dcc.Input(
                                                                                className="input",
                                                                                type="password",
                                                                                placeholder="Enter your password",
                                                                                id="pwd-box",
                                                                                name="password",
                                                                                autoComplete="off",
                                                                            )
                                                                        ],
                                                                    ),
                                                                ],
                                                            ),
                                                            html.Div(
                                                                className="field",
                                                                children=[
                                                                    html.Div(
                                                                        className="control",
                                                                        children=[
                                                                            html.Button(
                                                                                children="Login",
                                                                                n_clicks=0,
                                                                                type="submit",
                                                                                id="login-button",
                                                                                className="button is-primary",
                                                                            )
                                                                        ],
                                                                    )
                                                                ],
                                                            ),
                                                            html.Div(
                                                                children="",
                                                                id="output-state",
                                                            ),
                                                        ],
                                                        method="POST",
                                                    ),
                                                ],
                                            )
                                        ],
                                    )
                                ],
                            )
                        ],
                    )
                ],
            )
        ]
    )
