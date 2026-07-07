import dash
from dash import html, dcc
from flask_login import current_user
from pages.login import layout as login_layout
from utils.login_handler import get_accessible_pages_by_role, ACCOUNTS, require_login


dash.register_page(__name__, path="/", redirect_from=["/home"])


def layout():
    if current_user.is_authenticated:
        accessible_pages = get_accessible_pages_by_role(
            ACCOUNTS[current_user.id]["role"]
        )
        print(accessible_pages)
        return html.Div(
            [
                html.H1("Accessible Reports:", className="title"),
                html.Div(
                    [
                        html.Ul(
                            [
                                html.Li(dcc.Link(page, href=accessible_pages[page]))
                                for page in accessible_pages
                            ],
                        )
                    ],
                    style={"margin-left": "30px", "margin-top": "30px"},
                ),
            ]
        )
    else:
        return html.Div(
            [
                html.Label("You have not logged in. Please "),
                dcc.Link("login", href="/login"),
            ]
        )
