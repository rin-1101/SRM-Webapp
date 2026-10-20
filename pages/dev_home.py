import dash
from dash import html, dcc
from flask import request


dash.register_page(__name__, path="/dev-home", name="Dev Home")


EXCLUDED_PATHS = {
    "/dev-home",
    "/login",
    "/logout",
    "/permission",
}


def _page_title(page):
    return page.get("name") or page.get("title") or page.get("module") or page["path"]


def _visible_pages():
    pages = []
    for page in dash.page_registry.values():
        path = page.get("path")
        if not path or path in EXCLUDED_PATHS:
            continue
        pages.append(page)

    return sorted(pages, key=lambda page: _page_title(page).lower())


def _is_allowed_dev_host():
    """Allow Dev Home only when the browser URL is using port 8050."""
    return request.host.endswith(":8050")


def layout():
    if not _is_allowed_dev_host():
        return html.Div(
            [
                html.H1("Not available", className="title"),
                html.P("Dev Home is only available on srm.okadamanila.com:8050."),
                dcc.Link("Back home", href="/"),
            ],
            style={"padding": "24px"},
        )

    pages = _visible_pages()

    return html.Div(
        [
            html.H1("Dev Home", className="title"),
            html.P(
                "Development-only page index. This page does not require LDAP authentication.",
                className="subtitle",
            ),
            html.Div(
                [
                    html.Ul(
                        [
                            html.Li(
                                [
                                    dcc.Link(_page_title(page), href=page["path"]),
                                    html.Span(f"  ({page['path']})", style={"color": "#777"}),
                                ]
                            )
                            for page in pages
                        ]
                    )
                ],
                style={"marginLeft": "30px", "marginTop": "20px"},
            ),
        ],
        style={"padding": "24px"},
    )
