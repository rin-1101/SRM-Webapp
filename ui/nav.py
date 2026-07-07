from dash import html

nav_bar = html.Div(
    children=[
        html.Nav(
            className="navbar is-white has-shadow",
            children=[
                # Logo / Brand
                html.Div(
                    className="navbar-brand",
                    children=[
                        html.A(
                            className="navbar-item",
                            children=[
                                html.Img(
                                    src="./assets/home.png",
                                    style={"maxHeight": "50px"},
                                    className="py-2 px-2",
                                ),
                                html.Img(
                                    src="./assets/logo.png",
                                    style={"maxHeight": "50px"},
                                    className="py-2 px-2",
                                ),
                            ],
                            href="/home",  # Only one <a> tag is wrapping the logo images
                        ),
                        # The burger should not be an <a> tag
                        html.Div(
                            className="navbar-burger",
                            id="burger",
                            children=[
                                html.Span(),  # Line 1
                                html.Span(),  # Line 2
                                html.Span(),  # Line 3
                            ],
                            # Don't wrap burger button in <a> tag, use a <div> or button
                        ),
                    ],
                ),
                html.Div(
                    className="navbar-menu",
                    id="nav-links",
                    children=[
                        # Right Links
                        html.Div(
                            className="navbar-end",
                            children=[
                                html.Div(
                                    className="navbar-item",
                                    children=html.A(
                                        id="login-status",
                                        className="button is-primary has-text-white",
                                        children=["Login"],  # Add button text or content
                                        href="/login",  # Ensure the <a> tag is used properly for navigation
                                    ),
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        )
    ]
)
