"""Portrait-tablet ecommerce layout for shared shopping campaigns."""

from dash import dcc, html


def build_item_card(page, i, row, coding_tag=None, unavailable=False):
    """Build a touch-friendly catalogue card."""
    cfg = page.config
    assetspath = "/assets/inventory/{}/{}.png".format(cfg.assets_folder, row["ID"])
    if coding_tag and coding_tag != "DEFAULT":
        assetspath = "/assets/inventory/{}/{}/{}.png".format(
            cfg.assets_folder, coding_tag, row["ID"]
        )

    category = str(row.get("category", "Uncategorized") or "Uncategorized").strip()
    item_name = str(row.get("name", "Reward") or "Reward").strip()
    content = [
        html.Div(
            className="shop-product-image-wrap",
            children=[html.Img(
                src=assetspath,
                alt=item_name,
                className="shop-product-image",
            )],
        ),
        html.Div(
            className="shop-product-content",
            children=[
                html.Span(category, className="shop-product-category"),
                html.H3(item_name, className="shop-product-name"),
                html.Div(
                    className="shop-product-meta",
                    children=[
                        html.Strong(
                            "{} {}".format(row["cost"], cfg.currency_label),
                            className="shop-product-price",
                        ),
                    ],
                ),
                html.Span("View details", className="shop-product-action"),
            ],
        ),
    ]
    if not cfg.view_only:
        content.append(
            html.Span(
                "0",
                id=page.wid("item-qty", int(i)),
                className="shop-selected-quantity",
            )
        )

    quick_add = cfg.quick_add and not cfg.view_only
    card_children = [html.Button(
        id=page.wid("card", int(i)),
        className=(
            "shop-product-card is-unavailable"
            if unavailable else "shop-product-card"
        ),
        n_clicks=0,
        children=content,
    )]
    if quick_add:
        card_children.append(html.Button(
            "Add to Cart",
            id=page.wid("quick-add", int(i)),
            className="shop-quick-add-button",
            n_clicks=0,
            disabled=unavailable,
        ))

    return html.Div(
        id=page.wid(
            "catalog-item",
            "{}|{}|{}".format(
                page.category_slug(category),
                page.category_slug(item_name),
                int(i),
            ),
        ),
        className="shop-catalogue-cell{}".format(
            " has-quick-add" if quick_add else ""
        ),
        style={},
        children=card_children,
    )


def _wallet_metric(page, title, title_id, input_id, is_balance=False):
    return html.Div(
        className="shop-wallet-metric{}".format(" is-balance" if is_balance else ""),
        children=[
            html.Span(title, id=page.id(title_id), className="shop-wallet-label"),
            dcc.Input(
                id=page.id(input_id),
                type="text",
                placeholder="0",
                className="shop-wallet-value",
                disabled=True,
            ),
        ],
    )


def _item_modal(page):
    cfg = page.config
    body = [
        html.Div(
            className="shop-modal-image-wrapper",
            children=[dcc.Loading(
                type="circle",
                children=[html.Img(
                    id=page.id("item-image"),
                    className="shop-modal-image",
                )],
            )],
        ),
        html.H3(id=page.id("item-name"), className="shop-modal-title"),
        html.P(id=page.id("item-cost"), className="shop-modal-cost"),
        html.P(
            id=page.id("category-limit-warning"),
            className="shop-category-warning",
        ),
    ]
    if not cfg.view_only:
        body += [
            html.Div(
                className="shop-quantity-stepper",
                children=[
                    html.Button(
                        "-",
                        id=page.id("sub-button"),
                        className="shop-stepper-button",
                    ),
                    html.Div(
                        "0",
                        id=page.id("qty"),
                        className="shop-stepper-value",
                    ),
                    html.Button(
                        "+",
                        id=page.id("add-button"),
                        className="shop-stepper-button",
                    ),
                ],
            ),
            html.Button(
                "ADD TO BASKET",
                id=page.id("item-add"),
                className="shop-primary-button shop-add-button",
            ),
        ]
    else:
        body.append(html.Div("0", id=page.id("qty"), style={"display": "none"}))

    return html.Div(
        id=page.id("item-description"),
        className="modal shop-bottom-sheet",
        children=[
            html.Div(className="modal-background"),
            html.Div(
                className="modal-card modal-card-shop shop-item-sheet",
                children=[
                    html.Header(
                        className="modal-card-head",
                        children=[
                            html.Div(children=[
                                html.Span("REWARD", className="shop-section-kicker"),
                                html.P("Item details", className="modal-card-title"),
                            ]),
                            html.Button(
                                id=page.id("close-button"),
                                className="delete",
                                n_clicks=0,
                                **{"aria-label": "Close item details"}
                            ),
                        ],
                    ),
                    html.Section(
                        className="modal-card-body shop-modal-body",
                        children=body,
                    ),
                ],
            ),
        ],
    )


def _redeem_modal(page):
    return html.Div(
        id=page.id("redeem-modal"),
        className="modal shop-bottom-sheet",
        children=[
            html.Div(className="modal-background"),
            html.Div(
                className="modal-card modal-card-shop shop-basket-sheet",
                children=[
                    html.Header(
                        className="modal-card-head",
                        children=[
                            html.Div(children=[
                                html.Span("BASKET", className="shop-section-kicker"),
                                html.P(
                                    "Confirm your rewards",
                                    className="modal-card-title",
                                ),
                            ]),
                            html.Button(
                                id=page.id("cancel-redeem-button"),
                                className="delete",
                                **{"aria-label": "Close basket"}
                            ),
                        ],
                    ),
                    html.Section(
                        className="modal-card-body",
                        children=[
                            html.Div(
                                id=page.id("modal-basket-content"),
                                className="shop-basket-content",
                            ),
                            html.P(
                                "Confirmed redemptions cannot be amended.",
                                className="shop-basket-warning",
                            ),
                        ],
                    ),
                    html.Footer(
                        className="modal-card-foot shop-basket-actions",
                        children=[
                            html.Button(
                                "CONFIRM REDEEM",
                                id=page.id("confirm-redeem-button"),
                                className="shop-primary-button",
                            ),
                            html.Button(
                                "CONTINUE SHOPPING",
                                id=page.id("cancel-redeem-button2"),
                                className="shop-secondary-button",
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )


def build_tablet_layout(page):
    """Build the shared portrait-tablet storefront."""
    cfg = page.config
    folder = cfg.assets_folder

    children = [
        html.Link(rel="stylesheet", href="/assets/shop/tablet-ecommerce.css"),
        html.Link(rel="stylesheet", href="/assets/{}/style.css".format(folder)),
        dcc.Location(id=page.id("url"), refresh=True),
        dcc.Interval(
            id=page.id("interval-refresh"),
            interval=3000,
            n_intervals=0,
            disabled=True,
        ),
        html.Div(
            className=(
                "shop-style-picker"
                if len(cfg.style_options) > 1 and not cfg.bdcoding
                else "shop-style-picker is-hidden"
            ),
            children=[dcc.RadioItems(
                id=page.id("style-selector"),
                options=cfg.style_options,
                value=cfg.default_style,
                className="shop-style-radio-group",
                inputClassName="shop-style-radio-input",
                labelClassName="shop-style-radio-label",
            )],
        ),
        html.Div(
            className="shop-page-logo-wrap",
            children=[html.Img(
                src="/assets/{}/{}".format(folder, cfg.logo_filename),
                alt="Campaign logo",
                className="shop-page-logo",
            )],
        ),
        html.Button(
            "Refresh",
            id=page.id("back-button"),
            className="shop-floating-refresh",
            n_clicks=0,
        ),
        html.Img(
            id=page.id("logo-main"),
            src="/assets/{}/{}".format(folder, cfg.logo_filename),
            className="shop-callback-logo",
            style={"display": "none"},
        ),
        html.Main(
            className="shop-mobile-content",
            children=[
                html.Section(
                    id=page.id("main-container-items"),
                    className="shop-member-wallet",
                    children=[
                        html.Div(
                            className="shop-member-heading",
                            children=[
                                html.Div(children=[
                                    html.Span(
                                        "MEMBER",
                                        className="shop-section-kicker",
                                    ),
                                    html.H1(
                                        cfg.member_title,
                                        className="shop-section-title",
                                    ) if cfg.member_title else None,
                                ]),
                            ],
                        ),
                        html.Div(
                            className="shop-member-search-row",
                            children=[
                                dcc.Input(
                                    id=page.id("uid-textbox"),
                                    type="number",
                                    placeholder=cfg.search_placeholder,
                                    className="shop-member-search-input",
                                    autoComplete="off",
                                ),
                                html.Button(
                                    "Check",
                                    id=page.id("export-button"),
                                    n_clicks=0,
                                    className="shop-primary-button",
                                ),
                            ],
                        ),
                        html.Div(
                            className="shop-member-identity-row",
                            children=[
                                html.Label(
                                    className="shop-identity-field",
                                    children=[
                                        html.Span("INITIALS"),
                                        dcc.Input(
                                            id=page.id("initials-textbox"),
                                            type="text",
                                            placeholder="--",
                                            disabled=True,
                                        ),
                                    ],
                                ),
                                html.Label(
                                    className="shop-identity-field",
                                    children=[
                                        html.Span("TIER"),
                                        dcc.Input(
                                            id=page.id("tier-textbox"),
                                            type="text",
                                            placeholder="--",
                                            disabled=True,
                                        ),
                                    ],
                                ),
                            ] + ([
                                html.Label(
                                    className=(
                                        "shop-identity-field "
                                        "shop-tagging-field"
                                    ),
                                    children=[
                                        html.Span("CATEGORY GROUP"),
                                        dcc.Input(
                                            id=page.id("tagging-textbox"),
                                            type="text",
                                            placeholder="--",
                                            disabled=True,
                                        ),
                                    ],
                                )
                            ] if cfg.bdcoding else []),
                        ),
                    ],
                ),
                html.Div(
                            id=page.id("credits-section"),
                            className="shop-wallet-strip shop-wallet-sticky",
                            style={"display": "none"},
                            children=[
                                html.Div(
                                    id=page.id("credits-main-container"),
                                    className="shop-wallet-grid",
                                    children=[
                                        _wallet_metric(
                                            page,
                                            cfg.page_title_earned,
                                            "title-credits",
                                            "tp-display",
                                        ),
                                        _wallet_metric(
                                            page,
                                            cfg.page_title_redeemed,
                                            "title-red",
                                            "tp-redeem",
                                        ),
                                        _wallet_metric(
                                            page,
                                            cfg.page_title_balance,
                                            "title-tp-bal",
                                            "tp-balance",
                                            is_balance=True,
                                        ),
                                    ],
                                )
                            ],
                        ),
                html.Div(
                    id=page.id("Error-text"),
                    className="shop-validation-message",
                ),
                html.Section(
                    className="shop-catalogue-section",
                    children=[
                        html.Div(
                            className="shop-catalogue-heading",
                            children=[
                                html.Div(children=[
                                    html.Span(
                                        "CATALOGUE",
                                        className="shop-section-kicker",
                                    ),
                                    html.H2(
                                        "Eligible rewards",
                                        className="shop-section-title",
                                    ),
                                ]),
                                html.Span(
                                    "Tap an item for details",
                                    className="shop-catalogue-hint",
                                ),
                            ],
                        ),
                        html.Div(
                            className="shop-catalogue-tools",
                            children=[
                                dcc.Input(
                                    id=page.id("catalog-search"),
                                    type="search",
                                    placeholder="Search rewards",
                                    className="shop-catalogue-search",
                                    debounce=True,
                                ),
                                dcc.RadioItems(
                                    id=page.id("category-filter"),
                                    options=[
                                        {"label": "ALL", "value": "all"}
                                    ],
                                    value="all",
                                    className="shop-category-chips",
                                    inputClassName=(
                                        "shop-category-chip-input"
                                    ),
                                    labelClassName=(
                                        "shop-category-chip-label"
                                    ),
                                ),
                            ],
                        ),
                        html.Div(
                            id=page.id("items-grid"),
                            className="shop-items-grid is-hidden",
                            children=[],
                        ),
                    ],
                ),
            ],
        ),
        _item_modal(page),
        dcc.Store(id=page.id("visible-rows"), data=[]),
        dcc.Store(id=page.id("item-limit-store"), data=0),
        dcc.Store(id=page.id("modal-item-index"), data={}),
        dcc.Store(id=page.id("current-quantity"), data=0),
        dcc.Store(id=page.id("token"), data=0),
        dcc.Store(id=page.id("red"), data=0),
        dcc.Store(id=page.id("selected-item-id"), data=None),
        dcc.Store(id=page.id("df-length"), data=0),
        dcc.Store(id=page.id("details-visibility"), data=False),
        dcc.Store(id=page.id("prev-redeemed-by-cat"), data={}),
        dcc.Store(id=page.id("coding-tag"), data=None),
    ]

    if not cfg.view_only:
        children += [
            dcc.Store(id=page.id("quantities-store"), data={}),
            dcc.Store(id=page.id("cart-value"), data=0),
            dcc.Store(id=page.id("last-confirm-ts"), data=0),
            _redeem_modal(page),
            html.Footer(
                id=page.id("redeem-footer"),
                className="shop-redeem-footer footer is-hidden",
                style={"display": "none"},
                children=[
                    html.Div(
                        className="shop-cart-summary",
                        children=[
                            html.Span(
                                "0 ITEMS",
                                id=page.id("cart-item-count"),
                                className="shop-cart-count",
                            ),
                            html.Div(children=[
                                html.Span(
                                    "TOTAL",
                                    className="shop-cart-total-label",
                                ),
                                html.Strong(
                                    children=[
                                        html.Span(
                                            "0",
                                            id=page.id("total-value"),
                                        ),
                                        " {}".format(cfg.currency_label),
                                    ],
                                    className="shop-cart-total",
                                ),
                            ]),
                        ],
                    ),
                    html.Button(
                        "VIEW BASKET",
                        id=page.id("redeem-button"),
                        className="shop-basket-button",
                    ),
                    html.Div(
                        id=page.id("redeem-status"),
                        className="shop-redeem-status",
                    ),
                ],
            ),
        ]

    content = children
    if cfg.background_mask:
        content = [
            html.Div(
                className="shop-background-mask",
                style={"backgroundColor": cfg.background_mask},
            ),
            html.Div(className="shop-layer-content", children=children),
        ]

    container_class = (
        "shop-main-container shop-tablet-commerce "
        "shop-theme-{}".format(cfg.default_style)
    )
    if cfg.low_power_mode:
        container_class += " shop-low-power"

    return html.Div(
        id=page.id("main-container"),
        className=container_class,
        style=page.get_background_style_for_tag(),
        children=content,
    )
