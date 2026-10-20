"""Dash layout construction for shopping pages."""

import pandas as pd
from dash import dcc, html

from .tablet_layout import build_item_card, build_tablet_layout


class ShopLayoutMixin(object):
    def _build_item_card(
        self,
        i: int,
        row: pd.Series,
        coding_tag: str = None,
        unavailable: bool = False,
    ) -> html.Div:
        return build_item_card(self, i, row, coding_tag, unavailable)
        """Standalone card builder ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â also used by `display_items()`."""
        folder = self.config.assets_folder
        px = self.config.css_prefix
        assetspath = f"/assets/inventory/{folder}/{row['ID']}.png"
        if(coding_tag and coding_tag != "DEFAULT"):
            assetspath = f"/assets/inventory/{folder}/{coding_tag}/{row['ID']}.png"
        return html.Div(
            className="column is-half-tablet is-one-third-desktop shop-item-column",
            children=[
                html.Button(
                    id=self.wid("card", int(i)),
                    className=f"card shop-card",
                    n_clicks=0,
                    children=[
                        html.Div(
                            className="card-image",
                            children=[html.Img(
                                src=assetspath,
                                className=f"image-card-{px}",
                            )],
                        ),
                        html.Div(
                            className=f"card-content has-text-centered shop-card-content",
                            children=[
                                html.P(row["name"], className=f"title is-6 shop-card-title"),
                                html.P(f"{row['cost']} {self.config.currency_label}",
                                       className=f"subtitle is-7 shop-card-subtitle"),
                                html.Div(
                                    [html.P("Quantity:"),
                                     html.Span("0", id=self.wid("item-qty", int(i)))],
                                    className=f"shop-quantity",
                                ) if not self.config.view_only else None,
                            ],
                        ),
                    ],
                )
            ],
        )

    def _layout(self) -> html.Div:
        return build_tablet_layout(self)

        cfg = self.config
        folder = cfg.assets_folder
        px = cfg.css_prefix

        children = [
            html.Link(rel="stylesheet", href=f"/assets/{folder}/style.css"),
            dcc.Location(id=self.id("url"), refresh=True),
            dcc.Interval(id=self.id("interval-refresh"), interval=3000, n_intervals=0, disabled=True),

            html.Div(
                className="shop-style-picker" if (len(cfg.style_options) > 1 and not cfg.bdcoding) else "shop-style-picker is-hidden",
                children=[dcc.RadioItems(
                    id=self.id("style-selector"),
                    options=cfg.style_options,
                    value=cfg.default_style,
                    className="shop-style-radio-group",
                    inputClassName="shop-style-radio-input",
                    labelClassName="shop-style-radio-label",
                )],
            ),

            # Logo
            html.Div(
                className="shop-logo-wrap",
                children=[html.Img(
                    id=self.id("logo-main"),
                    src=f"/assets/{folder}/{cfg.logo_filename}",
                    className="shop-main-logo",
                )],
            ),

            # Refresh button
            html.Div(
                id=self.id("back-button-container"),
                className="shop-refresh-wrap",
                children=[html.Button("Refresh", id=self.id("back-button"),
                                       className="button is-text", style={"color": "white"})],
            ),

            # Player search section
            html.Section(
                className="section is-vcentered is-centered is-flex is-fullheight",
                children=[
                    html.Div(
                        id=self.id("main-container-items"),
                        className="columns is-vcentered is-centered is-flex is-fullheight shop-search-container",
                        children=[
                            html.Div(
                                className="column is-one-quarter has-text-centered",
                                children=[html.Img(id=self.id("logo"), src=cfg.fallback_logo_src)],
                            ),
                            html.Div(
                                className="column shop-search-panel",
                                children=[
                                    html.Div(className="columns is-gapless", children=[
                                        html.Div(className="column is-two-thirds", children=[
                                            html.Div(className=f"search-box box-{px}", children=[
                                                dcc.Input(
                                                    id=self.id("uid-textbox"),
                                                    type="number",
                                                    placeholder=cfg.search_placeholder,
                                                    className="search-input input is-medium has-text-centered",
                                                    autoComplete="off",
                                                    style={"width": "100%"},
                                                )
                                            ])
                                        ]),
                                        html.Div(
                                            className="column is-one-third",
                                            style={"display": "flex", "justifyContent": "center", "alignItems": "center"},
                                            children=[html.Button(
                                                "Check", id=self.id("export-button"), n_clicks=0,
                                                className=f"button-shop button", style={"width": "100%"},
                                            )],
                                        ),
                                    ]),
                                    html.Div(className="columns is-centered", children=[
                                        html.Div(className="column is-one-third", children=[
                                            html.Div(className=f"search-box box-{px}", children=[
                                                dcc.Input(id=self.id("initials-textbox"), type="text",
                                                          placeholder="Initials",
                                                          className="search-input input is-medium has-text-centered",
                                                          disabled=True)
                                            ])
                                        ]),
                                        html.Div(className="column is-one-third" if cfg.bdcoding else "column is-two-thirds", children=[
                                            html.Div(className=f"search-box box-{px}", children=[
                                                dcc.Input(id=self.id("tier-textbox"), type="text",
                                                          placeholder="Tier",
                                                          className="search-input input is-medium has-text-centered",
                                                          disabled=True)
                                            ])
                                        ]),
                                    ] + ([
                                        html.Div(className="column is-one-third", children=[
                                            html.Div(className=f"search-box box-{px}", children=[
                                                dcc.Input(id=self.id("tagging-textbox"), type="text",
                                                          placeholder="Tagging",
                                                          className="search-input input is-medium has-text-centered",
                                                          disabled=True)
                                            ])
                                        ]),
                                    ] if cfg.bdcoding else [])),
                                ],
                            ),
                        ],
                    )
                ],
            ),

            html.Div(id=self.id("Error-text"), className="has-text-danger has-text-centered"),

            # Item details modal
            html.Div(
                id=self.id("item-description"),
                className="modal",
                children=[
                    html.Div(className="modal-background"),
                    html.Div(className=f"modal-card modal-card-shop shop-card", children=[
                        html.Header(className="modal-card-head", children=[
                            html.P("Item Details", className="modal-card-title"),
                            html.Button(id=self.id("close-button"), className="delete", n_clicks=0),
                        ]),
                        html.Section(className=f"modal-card-body shop-modal-body", children=[
                            html.Div(className=f"shop-modal-content", children=[
                                html.Figure(className=f"image shop-modal-image-wrapper", children=[
                                    dcc.Loading(type="circle", children=[
                                        html.Img(id=self.id("item-image"), className=f"shop-modal-image")
                                    ])
                                ]),
                                html.H3(id=self.id("item-name"), className=f"title is-5 has-text-centered shop-modal-title"),
                                html.P(id=self.id("item-cost"), className=f"subtitle is-6 has-text-centered shop-modal-cost"),
                                html.P(id=self.id("category-limit-warning"),
                                       className="has-text-warning has-text-centered is-size-7"),
                            ] + ([
                                html.Div(className=f"field has-addons has-addons-centered shop-quantity-field", children=[
                                    html.Button("-", id=self.id("sub-button"), className="button is-light"),
                                    html.Div("0", id=self.id("qty"), className="button is-static"),
                                    html.Button("+", id=self.id("add-button"), className="button is-light"),
                                ]),
                                html.Div(className="has-text-centered", children=[
                                    html.Button("Add to Cart", id=self.id("item-add"),
                                                 className="button is-success is-fullwidth")
                                ]),
                            ] if not cfg.view_only else [])),
                        ]),
                    ]),
                ],
            ),

            # Stores common to both modes
            dcc.Store(id=self.id("visible-rows"), data=[]),
            dcc.Store(id=self.id("item-limit-store"), data=0),
            dcc.Store(id=self.id("modal-item-index"), data={}),
            dcc.Store(id=self.id("current-quantity"), data=0),
            dcc.Store(id=self.id("token"), data=0),
            dcc.Store(id=self.id("red"), data=0),
            dcc.Store(id=self.id("selected-item-id"), data=None),
            dcc.Store(id=self.id("df-length"), data=0),
            dcc.Store(id=self.id("details-visibility"), data=False),
            dcc.Store(id=self.id("prev-redeemed-by-cat"), data={}),
            dcc.Store(id=self.id("coding-tag"), data=None),

            # TP credits section
            html.Div(
                id=self.id("credits-section"),
                style={"display": "none"},
                children=[
                    html.Div(
                        id=self.id("credits-main-container"),
                        className=f"shop-credits-container columns is-centered is-vcentered is-mobile",
                        children=[
                            html.Div(className="column is-3", children=[
                                html.Section(className="section has-text-centered", children=[
                                    html.H2(cfg.page_title_earned, id=self.id("title-credits"), className=f"shop-title title is-4"),
                                    html.Div(className=f"is-flex is-justify-content-center search-box box-{px}", children=[
                                        dcc.Input(id=self.id("tp-display"), type="text", placeholder="0",
                                                  className="input is-medium has-text-centered search-input", disabled=True)
                                    ])
                                ])
                            ]),
                            html.Div(className="column is-3", children=[
                                html.Section(className="section has-text-centered", children=[
                                    html.H2(cfg.page_title_redeemed, id=self.id("title-red"), className=f"shop-title title is-4"),
                                    html.Div(className=f"is-flex is-justify-content-center search-box box-{px}", children=[
                                        dcc.Input(id=self.id("tp-redeem"), type="text", placeholder="0",
                                                  className="input is-medium has-text-centered search-input", disabled=True)
                                    ])
                                ])
                            ]),
                            html.Div(className="column is-4", children=[
                                html.Section(className="section has-text-centered", children=[
                                    html.H2(cfg.page_title_balance, id=self.id("title-tp-bal"), className=f"shop-title title is-4"),
                                    html.Div(className=f"is-flex is-justify-content-center search-box box-{px}", children=[
                                        dcc.Input(id=self.id("tp-balance"), type="text", placeholder="0",
                                                  className="input is-medium has-text-centered search-input", disabled=True)
                                    ])
                                ])
                            ]),
                        ],
                    )
                ],
            ),

            # Items grid
            html.Section(
                className="section",
                children=[html.Div(
                    id=self.id("items-grid"),
                    className=f"shop-items-grid columns is-multiline is-mobile is-centered",
                    style={"maxWidth": "100vw", "margin": "0 auto"},
                    children=[],
                )],
            ),
        ]

        if not cfg.view_only:
            children += [
                dcc.Store(id=self.id("quantities-store"), data={}),
                dcc.Store(id=self.id("cart-value"), data=0),
                dcc.Store(id=self.id("last-confirm-ts"), data=0),

                # Redeem confirmation modal
                html.Div(
                    id=self.id("redeem-modal"),
                    className="modal",
                    children=[
                        html.Div(className="modal-background"),
                        html.Div(className=f"modal-card modal-card-shop shop-card", children=[
                            html.Header(className="modal-card-head", children=[
                                html.P("Confirm Your Basket", className="modal-card-title"),
                                html.Button("", id=self.id("cancel-redeem-button"), className="delete"),
                            ]),
                            html.Section(className="modal-card-body", children=[
                                html.Div(id=self.id("modal-basket-content")),
                                html.P("Upon pressing CONFIRM, no amendments may be made.",
                                       className="has-text-danger is-size-7 has-text-centered"),
                            ]),
                            html.Footer(className="modal-card-foot", children=[
                                html.Button("Confirm Redeem", id=self.id("confirm-redeem-button"), className="button is-danger"),
                                html.Button("Cancel", id=self.id("cancel-redeem-button2"), className="button"),
                            ]),
                        ]),
                    ],
                ),

                # Redeem footer
                html.Footer(
                    className=f"shop-redeem-footer footer is-fixed-bottom has-text-centered",
                    id=self.id("redeem-footer"),
                    style={"display": "none"},
                    children=[
                        html.Div(id=self.id("redeem-status"), className="has-text-success"),
                        html.Div([html.Span("Total Value: "), html.Span("0", id=self.id("total-value"))]),
                        html.Button("REDEEM", id=self.id("redeem-button"),
                                     className=f"button-shop button is-primary is-medium"),
                    ],
                ),
            ]

        background_style = self.get_background_style_for_tag(cfg.bdcoding_default_tag)

        if cfg.background_mask:
            children = [
                html.Div(
                    style={
                        "position": "fixed",
                        "top": 0,
                        "left": 0,
                        "right": 0,
                        "bottom": 0,
                        "backgroundColor": cfg.background_mask,
                        "pointerEvents": "none",
                        "zIndex": 0,
                    }
                ),
                html.Div(children=children, style={"position": "relative", "zIndex": 1}),
            ]

        return html.Div(style=background_style,
                         className=f"shop-main-container shop-theme-{self.get_style_for_tag(cfg.bdcoding_default_tag)}",
                         id=self.id("main-container"), children=children)

    @property
    def layout(self):
        """Expose as `layout = page.layout` (or `layout = page.layout()`,
        both work since Dash accepts a callable or a value)."""
        def _make():
            return html.Div(id=self.id("main-cont"), children=self._layout())
        return _make

    # ------------------------------------------------------------
