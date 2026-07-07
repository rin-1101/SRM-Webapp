from dash import html

footer = html.Footer(
    className="footer has-text-centered is-flex-align-items-flex-end mt-auto",
    children=[
        html.Div(
            className="content has-text-centered",
            children=[
                html.P(
                    children=[
                        "We have no dedicated QA. Please contact us, ",
                        html.A(
                            "here ",
                            href="mailto:SMGamingAnalytics@okadamanila.com?subject=Dashboard Feedback",
                        ),
                        "for any feedback / bug reports.",
                        html.Br(),
                        "Made with ",
                        html.Img(
                            src="./assets/heart.png",
                            style={"verticalAlign": "middle", "height": "30px"},
                            className="py-2 px-2",
                        ),
                        "by SM Gaming Analytics",
                    ]
                )
            ],
        )
    ],
)
