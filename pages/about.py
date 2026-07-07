import dash
from dash import html

dash.register_page(__name__, path="/about")  # About page

layout = html.Div(
    [
        html.H1("About Us"),
        html.P("Welcome to the Gaming Analytics Dashboard!"),
        html.P(
            "Here's a fun Easter egg! Solve the probability problem below to test your skills:"
        ),
        html.H3("The Probability Problem:"),
        html.P(
            "Imagine you are designing a game with loot boxes. Each loot box contains a rare item with a probability of 0.2 "
            "and a common item with a probability of 0.8. You open 5 loot boxes. What is the probability that exactly 2 "
            "of the loot boxes contain rare items?"
        ),
        html.P("Hint: This is a binomial probability problem!"),
        html.Div(
            [
                html.H4("Formula:"),
                html.P("Use the binomial distribution formula:"),
                html.P(
                    "P(X = k) = (n choose k) * p^k * (1 - p)^(n - k)"
                ),
                html.P("Where:"),
                html.P("n = number of trials (in this case, 5 loot boxes)"),
                html.P("k = number of rare items (in this case, 2)"),
                html.P("p = probability of a rare item in a loot box (0.2)"),
            ]
        ),
        html.P("Take a moment and try to solve it!"),
    ]
)
