import dash
from dash import html, dcc

dash.register_page(__name__, path="/permission")

layout = html.Div(
    [
        "Sorry, you do not have permission to view this content, please get with your administrator if you think this is wrong",
        html.Br(),
        dcc.Link("Back home", href="/"),
    ]
)
