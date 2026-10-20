import ntpath

import dash
from dash import html

from utils.login_handler import require_login, restricted_page


PAGE_PATH = "/ssl"


dash.register_page(__name__, path=PAGE_PATH, name="SSL Certificate")
require_login(
    __name__, access_level=restricted_page[PAGE_PATH]["access_level"]
)


def _file_details(title, directory, filename):
    return html.Div(
        [
            html.H2(title, className="title is-5"),
            html.Div(
                [
                    html.Strong("File path"),
                    html.Code(directory),
                ],
                className="mb-4",
            ),
            html.Div(
                [
                    html.Strong("Filename"),
                    html.Code(filename),
                ],
            ),
        ],
        className="box",
    )


def layout():
    ssl_context = getattr(dash.get_app(), "ssl_context", None)

    if not isinstance(ssl_context, (tuple, list)) or len(ssl_context) != 2:
        return html.Section(
            [
                html.H1("SSL Certificate", className="title"),
                html.P(
                    "No SSL context is configured on the running Dash app.",
                    className="notification is-warning is-light",
                ),
            ],
            className="section",
            style={"maxWidth": "900px", "margin": "0 auto"},
        )

    certificate_file, private_key_file = map(str, ssl_context)
    certificate_directory, certificate_filename = ntpath.split(certificate_file)
    private_key_directory, private_key_filename = ntpath.split(private_key_file)

    return html.Section(
        [
            html.H1("SSL Certificate", className="title"),
            html.P(
                "These values are read from the running app.ssl_context.",
                className="notification is-info is-light",
            ),
            _file_details(
                "Certificate / full chain",
                certificate_directory,
                certificate_filename,
            ),
            _file_details(
                "Private key",
                private_key_directory,
                private_key_filename,
            ),
        ],
        className="section",
        style={"maxWidth": "900px", "margin": "0 auto"},
    )
