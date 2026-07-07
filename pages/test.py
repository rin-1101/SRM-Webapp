# import sys
# import dash
# import pandas as pd
# from dash import dcc, html, dash_table, Input, Output, State, callback, ctx, ALL
# from utils.paths import COMMS

# import plotly.graph_objects as go
# dash.register_page(__name__, path="testinggpt")


# # ---------- Sample data ----------
# months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
# revenue = [40, 25, 30, 32, 40, 25, 15, 30, 22, 16, 27, 25]
# orders = [27, 35, 56, 20, 26, 35, 25, 17, 18, 30, 10, 30]

# category_labels = ["Electronics", "Laptops", "iPhones"]
# category_values = [34, 28, 38]

# products_df = pd.DataFrame(
#     [
#         ["Electronics", "#24001", "$300", 455, "$4892"],
#         ["Shoes", "#24002", "$280", 678, "$3521"],
#         ["Laptop", "#24003", "$400", 431, "$6493"],
#         ["Mobile", "#24004", "$300", 781, "$7259"],
#     ],
#     columns=["Name", "Order ID", "Price", "Sold", "Sales"],
# )

# funnel_metrics = [
#     ("Product views", "10%", "5,465"),
#     ("Add to cart", "5%", "3,155"),
#     ("Checkout initiated", "5%", "3,044"),
#     ("Completed purchases", "12%", "5,891"),
# ]

# summary_cards = [
#     {
#         "title": "Total Sales",
#         "value": "$357,852.10",
#         "delta": "↗ 20.5%",
#         "note": "+30k last week",
#         "inverse": True,
#         "delta_color": "#2ecc71",
#     },
#     {
#         "title": "Visitors",
#         "value": "432,166",
#         "delta": "↗ 10%",
#         "note": "+2.8k this week",
#         "inverse": False,
#         "delta_color": "#2ecc71",
#     },
#     {
#         "title": "Total Orders",
#         "value": "853,467",
#         "delta": "↗ 5.3%",
#         "note": "+3k this week",
#         "inverse": False,
#         "delta_color": "#2ecc71",
#     },
#     {
#         "title": "Refunded",
#         "value": "612,762",
#         "delta": "↘ 9.2%",
#         "note": "+2k this week",
#         "inverse": False,
#         "delta_color": "#e74c3c",
#     },
# ]


# # ---------- Figure builders ----------
# def revenue_orders_figure():
#     fig = go.Figure()
#     fig.add_trace(
#         go.Scatter(
#             x=months,
#             y=revenue,
#             mode="lines+markers",
#             name="Revenue",
#             line={"width": 4, "color": "#111111", "shape": "spline", "smoothing": 0.6},
#             marker={"size": 7, "color": "#111111"},
#         )
#     )
#     fig.add_trace(
#         go.Scatter(
#             x=months,
#             y=orders,
#             mode="lines+markers",
#             name="Orders",
#             line={"width": 4, "color": "#8d8d8d", "shape": "spline", "smoothing": 0.6},
#             marker={"size": 7, "color": "#8d8d8d"},
#         )
#     )
#     fig.update_layout(
#         margin=dict(l=30, r=20, t=20, b=20),
#         paper_bgcolor="white",
#         plot_bgcolor="white",
#         legend=dict(orientation="h", y=1.12, x=0.3),
#         xaxis=dict(showgrid=False, zeroline=False, title=None),
#         yaxis=dict(showgrid=False, zeroline=False, title=None, range=[10, 60]),
#         font=dict(family="Arial", color="#111111"),
#         height=320,
#     )
#     return fig


# def category_figure():
#     fig = go.Figure(
#         data=[
#             go.Pie(
#                 labels=category_labels,
#                 values=category_values,
#                 hole=0.0,
#                 sort=False,
#                 direction="clockwise",
#                 marker=dict(colors=["#111111", "#6f6f6f", "#d9d9d9"], line=dict(color="white", width=3)),
#                 textinfo="none",
#                 showlegend=False,
#             )
#         ]
#     )
#     fig.update_layout(
#         margin=dict(l=0, r=0, t=0, b=0),
#         paper_bgcolor="white",
#         height=220,
#     )
#     return fig


# # ---------- Components ----------
# def stat_card(card):
#     bg = "#111111" if card["inverse"] else "#f0f0f0"
#     fg = "white" if card["inverse"] else "#111111"
#     return html.Div(
#         [
#             html.Div(card["title"], style={"fontSize": "16px", "fontWeight": "600", "marginBottom": "18px"}),
#             html.Div(card["value"], style={"fontSize": "38px", "fontWeight": "700", "marginBottom": "14px"}),
#             html.Div(
#                 [
#                     html.Span(card["delta"], style={"color": card["delta_color"], "fontWeight": "700", "marginRight": "8px"}),
#                     html.Span(card["note"], style={"opacity": 0.9}),
#                 ],
#                 style={"fontSize": "15px"},
#             ),
#         ],
#         style={
#             "backgroundColor": bg,
#             "color": fg,
#             "padding": "22px 24px",
#             "borderRadius": "0px",
#             "height": "150px",
#             "display": "flex",
#             "flexDirection": "column",
#             "justifyContent": "center",
#             "boxSizing": "border-box",
#         },
#     )


# def side_nav_item(label, badge=None, chevron=False):
#     return html.Div(
#         [
#             html.Span(label),
#             html.Div(
#                 [
#                     html.Span("▾" if chevron else "", style={"fontSize": "18px"}),
#                     html.Span(
#                         str(badge) if badge is not None else "",
#                         style={
#                             "background": "#111111",
#                             "color": "white",
#                             "borderRadius": "999px",
#                             "padding": "2px 7px",
#                             "fontSize": "12px",
#                             "display": "inline-block" if badge is not None else "none",
#                             "marginLeft": "10px",
#                         },
#                     ),
#                 ],
#                 style={"marginLeft": "auto", "display": "flex", "alignItems": "center", "gap": "8px"},
#             ),
#         ],
#         style={
#             "display": "flex",
#             "alignItems": "center",
#             "fontSize": "18px",
#             "padding": "14px 18px",
#             "borderRadius": "10px",
#             "cursor": "pointer",
#         },
#     )


# def layout(): return html.Div(
#     [
#         # Sidebar
#         html.Div(
#             [
#                 html.Div("Ecommerce", style={"fontSize": "34px", "fontWeight": "700", "marginBottom": "28px"}),
#                 html.Hr(style={"border": "none", "borderTop": "2px solid #2a2a2a", "margin": "0 0 20px 0"}),
#                 html.Div(
#                     [
#                         side_nav_item("Overview"),
#                         side_nav_item("Product", chevron=True),
#                         side_nav_item("Customers", chevron=True),
#                         side_nav_item("Orders", badge=3),
#                         side_nav_item("Checkout"),
#                         side_nav_item("Settings"),
#                     ],
#                     style={"display": "flex", "flexDirection": "column", "gap": "4px"},
#                 ),
#                 html.Div(style={"flex": 1}),
#                 html.Hr(style={"border": "none", "borderTop": "2px solid #2a2a2a", "margin": "0 0 20px 0"}),
#                 html.Div("Help", style={"fontSize": "18px", "padding": "10px 18px"}),
#                 html.Div("Contact us", style={"fontSize": "18px", "padding": "10px 18px"}),
#                 html.Div("Log out", style={"fontSize": "18px", "padding": "10px 18px"}),
#             ],
#             style={
#                 "width": "23%",
#                 "minWidth": "260px",
#                 "maxWidth": "320px",
#                 "borderRight": "2px solid #2a2a2a",
#                 "padding": "28px 24px",
#                 "display": "flex",
#                 "flexDirection": "column",
#                 "height": "100vh",
#                 "boxSizing": "border-box",
#                 "backgroundColor": "#f8f8f8",
#             },
#         ),
#         # Main content
#         html.Div(
#             [
#                 html.Div(
#                     [
#                         html.Div(
#                             [
#                                 html.H1("Welcome back, Steve", style={"margin": 0, "fontSize": "46px"}),
#                                 html.Div(
#                                     "Here’s what’s happening with your store today",
#                                     style={"fontSize": "20px", "marginTop": "8px", "color": "#444"},
#                                 ),
#                             ]
#                         ),
#                         html.Div(
#                             [
#                                 html.Span("⌕", style={"fontSize": "28px"}),
#                                 html.Span("🔔", style={"fontSize": "24px"}),
#                                 html.Div(
#                                     "👤",
#                                     style={
#                                         "width": "48px",
#                                         "height": "48px",
#                                         "border": "2px solid #111111",
#                                         "borderRadius": "50%",
#                                         "display": "flex",
#                                         "alignItems": "center",
#                                         "justifyContent": "center",
#                                         "fontSize": "24px",
#                                     },
#                                 ),
#                                 html.Span("⌄", style={"fontSize": "28px"}),
#                             ],
#                             style={"display": "flex", "alignItems": "center", "gap": "18px"},
#                         ),
#                     ],
#                     style={"display": "flex", "justifyContent": "space-between", "alignItems": "flex-start", "marginBottom": "26px"},
#                 ),
#                 html.Div(
#                     [html.Div(stat_card(card), style={"flex": 1}) for card in summary_cards],
#                     style={"display": "grid", "gridTemplateColumns": "repeat(4, 1fr)", "gap": "14px", "marginBottom": "20px"},
#                 ),
#                 html.Div(
#                     [
#                         html.Div(
#                             [
#                                 html.H2("Revenue vs Orders", style={"fontSize": "26px", "margin": "6px 0 10px 0"}),
#                                 dcc.Graph(figure=revenue_orders_figure(), config={"displayModeBar": False}),
#                                 html.H2("Top Products", style={"fontSize": "26px", "margin": "8px 0 18px 0"}),
#                                 html.Div(
#                                     [
#                                         dcc.Input(
#                                             id="product-search",
#                                             type="text",
#                                             placeholder="Search",
#                                             style={
#                                                 "width": "46%",
#                                                 "padding": "12px 14px",
#                                                 "fontSize": "18px",
#                                                 "border": "2px solid #3a3a3a",
#                                                 "outline": "none",
#                                             },
#                                         ),
#                                         dcc.Dropdown(
#                                             id="time-filter",
#                                             options=[
#                                                 {"label": "This week", "value": "This week"},
#                                                 {"label": "This month", "value": "This month"},
#                                                 {"label": "This quarter", "value": "This quarter"},
#                                             ],
#                                             value="This week",
#                                             clearable=False,
#                                             searchable=False,
#                                             style={"width": "180px", "fontSize": "18px"},
#                                         ),
#                                     ],
#                                     style={"display": "flex", "justifyContent": "space-between", "marginBottom": "16px"},
#                                 ),
#                                 dash_table.DataTable(
#                                     id="products-table",
#                                     columns=[{"name": i, "id": i} for i in products_df.columns],
#                                     data=products_df.to_dict("records"),
#                                     style_table={"overflowX": "auto", "border": "1px solid #444"},
#                                     style_header={
#                                         "backgroundColor": "#a7a7a7",
#                                         "color": "white",
#                                         "fontWeight": "600",
#                                         "fontSize": "18px",
#                                         "textAlign": "center",
#                                         "border": "1px solid #444",
#                                         "padding": "14px",
#                                     },
#                                     style_cell={
#                                         "backgroundColor": "#efefef",
#                                         "color": "#111",
#                                         "fontSize": "18px",
#                                         "textAlign": "center",
#                                         "border": "1px solid #444",
#                                         "padding": "14px",
#                                         "fontFamily": "Arial",
#                                     },
#                                     style_data_conditional=[
#                                         {"if": {"row_index": "odd"}, "backgroundColor": "#f8f8f8"},
#                                     ],
#                                 ),
#                             ],
#                             style={"flex": 1, "paddingRight": "24px"},
#                         ),
#                         html.Div(
#                             [
#                                 html.Div(
#                                     [
#                                         html.Div("Sales by category", style={"fontSize": "24px", "fontWeight": "700"}),
#                                         html.Div("→", style={"fontSize": "34px"}),
#                                     ],
#                                     style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "18px"},
#                                 ),
#                                 html.Div(
#                                     [
#                                         html.Div(
#                                             [
#                                                 html.Span(style={"display": "inline-block", "width": "18px", "height": "10px", "background": "#111111", "marginRight": "8px"}),
#                                                 "Electronics",
#                                             ],
#                                             style={"fontSize": "15px"},
#                                         ),
#                                         html.Div(
#                                             [
#                                                 html.Span(style={"display": "inline-block", "width": "18px", "height": "10px", "background": "#6f6f6f", "marginRight": "8px"}),
#                                                 "Laptops",
#                                             ],
#                                             style={"fontSize": "15px"},
#                                         ),
#                                         html.Div(
#                                             [
#                                                 html.Span(style={"display": "inline-block", "width": "18px", "height": "10px", "background": "#d9d9d9", "marginRight": "8px"}),
#                                                 "iPhones",
#                                             ],
#                                             style={"fontSize": "15px"},
#                                         ),
#                                     ],
#                                     style={"display": "flex", "gap": "16px", "flexWrap": "wrap", "marginBottom": "8px"},
#                                 ),
#                                 dcc.Graph(figure=category_figure(), config={"displayModeBar": False}),
#                                 html.Div(
#                                     [
#                                         html.Div("Conversion Rate", style={"fontSize": "24px", "fontWeight": "700"}),
#                                         html.Div("→", style={"fontSize": "34px"}),
#                                     ],
#                                     style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginTop": "10px"},
#                                 ),
#                                 html.Div(
#                                     [
#                                         html.Span("5.65%", style={"fontSize": "34px", "fontWeight": "700", "marginRight": "8px"}),
#                                         html.Span("↗ 10%", style={"fontSize": "18px", "fontWeight": "700", "color": "#2ecc71"}),
#                                     ],
#                                     style={"margin": "14px 0 6px 0"},
#                                 ),
#                                 html.Div(
#                                     "↗",
#                                     style={
#                                         "marginLeft": "auto",
#                                         "width": "34px",
#                                         "height": "34px",
#                                         "border": "2px solid #111111",
#                                         "borderRadius": "8px",
#                                         "display": "flex",
#                                         "alignItems": "center",
#                                         "justifyContent": "center",
#                                         "fontSize": "20px",
#                                     },
#                                 ),
#                                 html.Div(
#                                     [
#                                         html.Div(
#                                             [
#                                                 html.Div(label, style={"fontSize": "16px", "fontWeight": "600", "marginBottom": "4px"}),
#                                                 html.Div(rate, style={"fontSize": "14px", "color": "#666"}),
#                                             ]
#                                         ),
#                                         html.Div(value, style={"fontSize": "16px", "fontWeight": "700"}),
#                                     ],
#                                     style={
#                                         "display": "flex",
#                                         "justifyContent": "space-between",
#                                         "alignItems": "center",
#                                         "padding": "18px 0",
#                                         "borderBottom": "2px solid #d0d0d0",
#                                     },
#                                 )
#                                 for label, rate, value in funnel_metrics
#                             ],
#                             style={
#                                 "width": "320px",
#                                 "borderLeft": "2px solid #d0d0d0",
#                                 "paddingLeft": "24px",
#                                 "boxSizing": "border-box",
#                             },
#                         ),
#                     ],
#                     style={"display": "flex", "alignItems": "stretch"},
#                 ),
#             ],
#             style={"flex": 1, "padding": "26px 22px 28px 22px", "boxSizing": "border-box", "backgroundColor": "white"},
#         ),
#     ],
#     style={
#         "display": "flex",
#         "fontFamily": "Arial, sans-serif",
#         "backgroundColor": "#ffffff",
#         "color": "#111111",
#         "minHeight": "100vh",
#     },
# )


# @callback(
#     Output("products-table", "data"),
#     Input("product-search", "value"),
#     Input("time-filter", "value"),
# )
# def filter_products(search_value, _time_filter):
#     df = products_df.copy()
#     if search_value:
#         term = search_value.lower().strip()
#         mask = df.apply(lambda row: row.astype(str).str.lower().str.contains(term).any(), axis=1)
#         df = df[mask]
#     return df.to_dict("records")
