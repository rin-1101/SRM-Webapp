"""
templates/shopping.py
======================

Reusable Dash "Shop" page template — generalizes the browse → add to
cart → redeem flow (originally built as `fire-horse.py`) so it can be
instantiated multiple times with different ID suffixes, data sources,
and campaign rules. Mirrors how `templates/raffle.py` powers the RFR /
RFRG draw pages.

Two usage modes are supported via `ShopConfig.view_only`:

* Transactional shop  — browse, add to cart, redeem (e.g. `fire-horse.py`)
* View-only catalogue — browse + item detail modal, no cart/redeem
  (e.g. `fire-horse-view.py`)

Quick start
-----------
    # pages/fire-horse.py
    import sys
    sys.path.append(ROOT)
    import dash
    from utils.paths import FIRE_HORSE
    from utils.login_handler import restricted_page, require_login
    from templates.shopping import ShopConfig, ShoppingPage

    config = ShopConfig(
        suffix="afhc",
        page_path=FIRE_HORSE,
        access_level=restricted_page[FIRE_HORSE]["access_level"],
        path_db=PATH_DB,
        path_data=PATH_DATA,
        path_inv=PATH_INV,
        path_tier_csv=PATH_TIER_CSV,
        assets_folder="afhc",
        campaign_start="2026-05-11 06:00:00",
        campaign_end="2026-06-07 05:59:00",
        redeemed_window_start="2026-06-01 06:00:00",
        redeemed_window_end="2026-06-07 06:00:00",
    )

    # Register + auth BEFORE instantiating, at module top level —
    # mirrors templates/raffle.py's working pattern.
    dash.register_page(__name__, path=config.page_path)
    require_login(__name__, access_level=config.access_level)

    page = ShoppingPage(__name__, config)
    layout = page.layout
    page.register_callbacks()

    # pages/fire-horse-view.py
    config = ShopConfig(..., suffix="afhc-view", view_only=True)
    dash.register_page(__name__, path=config.page_path)
    require_login(__name__, access_level=config.access_level)
    page = ShoppingPage(__name__, config)
    layout = page.layout
    page.register_callbacks()

Each `ShoppingPage` instance namespaces every component ID, store, and
callback under `config.suffix`, so multiple instances can coexist in the
same Dash app without collisions — exactly like the existing `-afhc`
suffix convention, just made configurable instead of hardcoded.
"""

import math
import re
import sqlite3
import time as time_module
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Tuple

import dash
import pandas as pd
from dash import (
    dcc, html, Input, Output, State, callback, ctx, ALL,
    clientside_callback, callback_context,
)
from dash.exceptions import PreventUpdate

from utils.login_handler import require_login

# These two come from the okada applications root, already on sys.path
# by the time a concrete page module imports this template.
from okada import LogService
from shop import ShopTransaction
from inventory import Inventory


# ============================================================
#  Configuration
# ============================================================

class ShopConfig(object):
    """
    Everything that differs between shop instances lives here.
    A concrete page (e.g. `fire-horse.py`) builds one of these and
    hands it to `ShoppingPage`; nothing else needs to change.

    Plain class (not @dataclass) for compatibility with Python 3.6,
    where `dataclasses` isn't in the standard library.
    """

    def __init__(
        self,
        # --- identity / routing -------------------------------------
        suffix,                       # e.g. "afhc", "afhc-view" — namespaces every ID
        page_path,                    # Dash route, e.g. FIRE_HORSE
        access_level,                 # passed straight to require_login()
        # --- storage paths -------------------------------------------
        path_db,                      # sqlite file containing prize_pool
        path_data,                    # folder for ShopTransaction (orders db)
        path_inv,                     # folder for Inventory (stock db)
        path_tier_csv,                # cached tier snapshot CSV
        db_filename="afhc.db",
        orders_table="orders",
        prize_table="prize_pool",
        # --- assets ----------------------------------------------------
        assets_folder="afhc",         # -> /assets/<folder>/style.css, logo.png,
                                       #    /assets/inventory/<folder>/<ID>.png
        fallback_logo_src="/assets/DEFAULT/logo-cream.png",
        css_prefix=None,              # CSS class prefix, e.g. "afhc" -> "afhc-card".
                                       # Defaults to `assets_folder` so an existing
                                       # per-shop stylesheet keeps working unmodified;
                                       # override explicitly if you want "shop-*"
                                       # classes shared across a common shop.css.
        # --- campaign rules ----------------------------------------------
        max_per_category=3,
        campaign_start="",            # "YYYY-MM-DD HH:MM:SS", TierPoint earn window
        campaign_end="",
        redeemed_window_start="",     # window used for per-category redeemed counts
        redeemed_window_end="",
        valid_tier_ids=(7, 15, 10022),
        tier_names=None,              # default set below; avoids mutable-default trap
        # --- copy / labels (override per-shop without touching layout code) -
        currency_label="TP",
        search_placeholder="Enter OM Number",
        page_title_earned="TP Earned",
        page_title_redeemed="TP Redeemed",
        page_title_balance="TP Balance",
        # --- behaviour ---------------------------------------------------
        view_only=False,              # True => no cart / redeem, browse only
        logger_name="shop-page",
        # --- dev / QA override: {om_number: forced_balance} -----------------
        balance_overrides=None,       # default set below; avoids mutable-default trap
    ):
        self.suffix = suffix
        self.page_path = page_path
        self.access_level = access_level

        self.path_db = path_db
        self.path_data = path_data
        self.path_inv = path_inv
        self.path_tier_csv = path_tier_csv
        self.db_filename = db_filename
        self.orders_table = orders_table
        self.prize_table = prize_table

        self.assets_folder = assets_folder
        self.fallback_logo_src = fallback_logo_src
        self.css_prefix = css_prefix if css_prefix is not None else assets_folder

        self.max_per_category = max_per_category
        self.campaign_start = campaign_start
        self.campaign_end = campaign_end
        self.redeemed_window_start = redeemed_window_start
        self.redeemed_window_end = redeemed_window_end
        self.valid_tier_ids = valid_tier_ids
        self.tier_names = tier_names if tier_names is not None else {
            7: "Supreme", 15: "Maharlika", 10022: "Maharlika"
        }

        self.currency_label = currency_label
        self.search_placeholder = search_placeholder
        self.page_title_earned = page_title_earned
        self.page_title_redeemed = page_title_redeemed
        self.page_title_balance = page_title_balance

        self.view_only = view_only
        self.logger_name = logger_name

        self.balance_overrides = balance_overrides if balance_overrides is not None else {}

        required = ["suffix", "page_path", "path_db", "path_data", "path_inv", "path_tier_csv"]
        missing = [name for name in required if not getattr(self, name)]
        if missing:
            raise ValueError("ShopConfig missing required field(s): {}".format(", ".join(missing)))


# ============================================================
#  Page
# ============================================================

class ShoppingPage:
    """
    Encapsulates layout + callbacks for one shop instance.

    Instantiate once per concrete page module and expose `.layout` as
    the module-level Dash `layout` callable.

    IMPORTANT: unlike an earlier version of this class, `dash.register_page()`
    and `require_login()` are NOT called automatically here. Call them
    yourself at the top level of the page module, exactly like
    `templates/raffle.py`'s pattern — Dash's page auto-discovery is more
    reliable when `register_page()` runs directly in the file it's walking,
    rather than one call-frame removed inside a template class:

        # pages/fire_horse.py
        dash.register_page(__name__, path=config.page_path)
        require_login(__name__, access_level=config.access_level)

        page = ShoppingPage(__name__, config)
        layout = page.layout
        page.register_callbacks()
    """

    def __init__(self, module_name: str, config: ShopConfig):
        self.config = config
        self.suffix = config.suffix
        self.module_name = module_name
        self.logger = LogService(config.logger_name).get_logger()

    def register_callbacks(self) -> None:
        """Wire up all callbacks for this shop instance. Call this explicitly
        from the page module after `dash.register_page()`/`require_login()`
        — see the class docstring."""
        self._register_callbacks()

    # ------------------------------------------------------------
    #  ID namespacing
    # ------------------------------------------------------------
    def id(self, name: str) -> str:
        """Return `name` suffixed for this shop instance, e.g. id('redeem-button') -> 'redeem-button-afhc'."""
        return f"{name}-{self.suffix}"

    def wid(self, component_type: str, index) -> dict:
        """Wildcard/pattern-matching ID, e.g. for {'type': 'card-afhc', 'index': N}."""
        return {"type": f"{component_type}-{self.suffix}", "index": index}

    # ------------------------------------------------------------
    #  Data access
    # ------------------------------------------------------------
    @staticmethod
    def get_loader():
        """Always return a fresh SQL loader. Import deferred so this module
        doesn't hard-require `okada.SQL` unless a real query is run."""
        from okada import SQL
        return SQL("halo").get_loader()

    @staticmethod
    def format_om(om) -> str:
        return f"OM{str(om).zfill(9)}"

    @staticmethod
    def extract_tier(category: str) -> Optional[int]:
        match = re.search(r"Tier\s*(\d+)", str(category))
        return int(match.group(1)) if match else None

    @staticmethod
    def get_gamedate(now: datetime) -> date:
        cutoff = now.replace(hour=6, minute=0, second=0, microsecond=0)
        return (now - timedelta(days=1)).date() if now < cutoff else now.date()

    def read_prize_pool(self) -> pd.DataFrame:
        """Read the full prize pool ordered by cost."""
        conn = sqlite3.connect(self.config.path_db)
        try:
            return pd.read_sql_query(
                f"SELECT * FROM {self.config.prize_table} ORDER BY cost ASC", conn
            )
        finally:
            conn.close()

    def get_tier(self, uid: str) -> str:
        """
        Return tier name for a given UID.
        Checks the cached CSV snapshot first, then falls back to SQL.
        """
        hist = pd.read_csv(self.config.path_tier_csv)
        hist["UniversalPlayerID"] = hist["UniversalPlayerID"].astype(str).str.strip()
        filtered = hist[hist["UniversalPlayerID"] == uid.strip()]
        if not filtered.empty:
            return filtered.iloc[0]["Tier"]

        cfg = self.config
        case_clauses = "\n".join(
            f"WHEN TierID = {tier_id} THEN '{name}'"
            for tier_id, name in cfg.tier_names.items()
        )
        tier_id_list = ", ".join(str(t) for t in cfg.valid_tier_ids)
        sql = f"""
            SELECT UniversalPlayerID,
                CASE
                    {case_clauses}
                    ELSE 'NA'
                END AS TierName
            FROM ENGAGEDB.dbo.UC_PL_Player p
            LEFT JOIN ENGAGEDB.dbo.UC_PL_Tier t ON t.PlayerID = p.PlayerID
            WHERE UniversalPlayerID = '{uid}'
              AND t.TierID IN ({tier_id_list})
        """
        result = self.get_loader().load_data(sql)
        return result.iloc[0]["TierName"] if not result.empty else "NA"

    def get_balance(self, uid: str) -> int:
        """Return total TP earned during the campaign window (ceiling)."""
        if uid in self.config.balance_overrides:
            return self.config.balance_overrides[uid]

        sql = f"""
            SELECT p.UniversalPlayerID AS uid, tp.PlayerID, SUM(tp.TierPoint) AS Sum_TP
            FROM [ENGAGEDB].[dbo].[UC_PL_Rating] r
            LEFT JOIN [ENGAGEDB].[dbo].[UC_PL_Player] p          ON r.PlayerID   = p.PlayerID
            LEFT JOIN [ENGAGEDB].[dbo].[UC_PL_TierPointDetailActual] tp ON r.RatingID = tp.RatingID
            WHERE r.TransactionDateTime >= '{self.config.campaign_start}'
              AND r.TransactionDateTime  < '{self.config.campaign_end}'
              AND p.UniversalPlayerID = '{uid}'
            GROUP BY p.UniversalPlayerID, tp.PlayerID
            ORDER BY p.UniversalPlayerID, tp.PlayerID
        """
        tp_earn = self.get_loader().load_data(sql)
        if tp_earn.empty:
            return 0
        tp_earn = tp_earn[tp_earn["Sum_TP"] > 0]
        tp_earn["uid"] = tp_earn["uid"].str.strip()
        return math.ceil(tp_earn["Sum_TP"].sum())

    def _shop_transaction(self) -> "ShopTransaction":
        return ShopTransaction(
            self.config.path_data, self.config.db_filename,
            self.config.orders_table, user=f"redeem-app-{self.suffix}",
        )

    def _inventory(self) -> "Inventory":
        return Inventory(
            self.config.path_inv, self.config.db_filename,
            self.config.prize_table, user=f"redeem-app-{self.suffix}",
        )

    def get_redeemed(self, uid: str) -> int:
        """Total TP already redeemed across ALL transactions."""
        return int(self._shop_transaction().get_total_redeemed(uid) or 0)

    def get_redeemed_per_category(self, uid: str, df: pd.DataFrame) -> Dict[str, int]:
        """Total quantity redeemed per category for a player, within the redeemed window."""
        name_to_cat: Dict[str, str] = (
            df[["name", "category"]]
            .drop_duplicates("name")
            .set_index("name")["category"]
            .to_dict()
        )
        return self._shop_transaction().get_redeemed_by_category(
            uid, name_to_cat,
            since=self.config.redeemed_window_start,
            until=self.config.redeemed_window_end,
        )

    def find_initials(self, om_number: str) -> str:
        sql = f"""
            SELECT [FirstName] AS fn, [LastName] AS ln
            FROM [ENGAGEDB].[dbo].[UC_PL_Player]
            WHERE UniversalPlayerID = '{om_number}'
        """
        result = self.get_loader().load_data(sql)
        return f"{result.loc[0, 'fn'][0]}.{result.loc[0, 'ln'][0]}."

    # ------------------------------------------------------------
    #  Business logic (pure functions — no I/O, easy to unit test)
    # ------------------------------------------------------------
    @staticmethod
    def allocate_payment(order_items: list, credits_balance: int, cp_balance: int = 0) -> list:
        """Allocate credits first, then CP, for each order item."""
        credits_balance = max(0, credits_balance)
        cp_balance = max(0, cp_balance)
        results = []
        for item in order_items:
            cost = item["total"]
            use_credits = min(cost, credits_balance)
            use_cp = min(cost - use_credits, cp_balance)
            credits_balance -= use_credits
            cp_balance -= use_cp
            results.append({**item, "credits_used": use_credits, "cp_used": use_cp})
        return results

    @staticmethod
    def calculate_total_value(quantities: dict, df: pd.DataFrame) -> float:
        total = 0
        for idx_str, qty in quantities.items():
            try:
                total += df.loc[int(idx_str), "cost"] * qty
            except KeyError:
                pass
        return total

    def _category_warning(self, category: str, prev_cat_counts: dict) -> str:
        prev_qty = int(prev_cat_counts.get(category, 0))
        limit = self.config.max_per_category
        if prev_qty >= limit:
            return f"⚠️ You have already redeemed the max ({limit}) for this category."
        if prev_qty > 0:
            return f"ℹ️ You have redeemed {prev_qty} of {limit} allowed for this category."
        return ""

    # ------------------------------------------------------------
    #  Layout
    # ------------------------------------------------------------
    def _build_item_card(self, i: int, row: pd.Series) -> html.Div:
        """Standalone card builder — also used by `display_items()`."""
        folder = self.config.assets_folder
        px = self.config.css_prefix
        return html.Div(
            className="column is-half",
            children=[
                html.Button(
                    id=self.wid("card", int(i)),
                    className=f"card shop-card",
                    n_clicks=0,
                    children=[
                        html.Div(
                            className="card-image",
                            children=[html.Img(
                                src=f"/assets/inventory/{folder}/{row['ID']}.png",
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
        cfg = self.config
        folder = cfg.assets_folder
        px = cfg.css_prefix

        children = [
            html.Link(rel="stylesheet", href=f"/assets/{folder}/style.css"),
            dcc.Location(id=self.id("url"), refresh=True),
            dcc.Interval(id=self.id("interval-refresh"), interval=3000, n_intervals=0, disabled=True),

            # Logo
            html.Div(
                style={"textAlign": "center"},
                children=[html.Img(
                    id=self.id("logo-main"),
                    src=f"/assets/{folder}/logo.png",
                    style={"height": "300px", "width": "auto", "maxWidth": "100%",
                           "objectFit": "contain", "marginBottom": "-30vh", "marginTop": "5vh"},
                )],
            ),

            # Refresh button
            html.Div(
                id=self.id("back-button-container"),
                style={"display": "flex", "justifyContent": "flex-end"},
                children=[html.Button("Refresh", id=self.id("back-button"),
                                       className="button is-text", style={"color": "white"})],
            ),

            # Player search section
            html.Section(
                className="section is-vcentered is-centered is-flex is-fullheight",
                children=[
                    html.Div(
                        id=self.id("main-container-items"),
                        className="columns is-vcentered is-centered is-flex is-fullheight",
                        style={"paddingTop": "30vh"},
                        children=[
                            html.Div(
                                className="column is-one-quarter has-text-centered",
                                children=[html.Img(id=self.id("logo"), src=cfg.fallback_logo_src)],
                            ),
                            html.Div(
                                className="column",
                                style={"marginRight": "5rem"},
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
                                        html.Div(className="column is-two-thirds", children=[
                                            html.Div(className=f"search-box box-{px}", children=[
                                                dcc.Input(id=self.id("tier-textbox"), type="text",
                                                          placeholder="Tier",
                                                          className="search-input input is-medium has-text-centered",
                                                          disabled=True)
                                            ])
                                        ]),
                                    ]),
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
                    html.Div(className=f"modal-card shop-card", children=[
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
            dcc.Store(id=self.id("df-length"), data=len(self.read_prize_pool().index)),
            dcc.Store(id=self.id("details-visibility"), data=False),
            dcc.Store(id=self.id("prev-redeemed-by-cat"), data={}),

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
                        html.Div(className=f"modal-card shop-card", children=[
                            html.Header(className="modal-card-head", children=[
                                html.P("Confirm Your Basket", className="modal-card-title"),
                                html.Button("X", id=self.id("cancel-redeem-button"), className="delete"),
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

        return html.Div(style={"width": "100vw", "height": "100vh", "backgroundImage": f"url('/assets/{folder}/bg.png')"},
                         className=f"shop-main-container",
                         id=self.id("main-container"), children=children)

    @property
    def layout(self):
        """Expose as `layout = page.layout` (or `layout = page.layout()`,
        both work since Dash accepts a callable or a value)."""
        def _make():
            return html.Div(id=self.id("main-cont"), children=self._layout())
        return _make

    # ------------------------------------------------------------
    #  Callbacks
    # ------------------------------------------------------------
    def _register_callbacks(self) -> None:
        cfg = self.config
        id_ = self.id
        wid = self.wid
        px = cfg.css_prefix

        # ---- 1. Build / refresh item grid on Check --------------------
        @callback(
            Output(id_("items-grid"), "children"),
            Input(id_("export-button"), "n_clicks"),
            State(id_("uid-textbox"), "value"),
            prevent_initial_call=True,
        )
        def display_items(n_clicks, om):
            if not n_clicks:
                return dash.no_update

            om_new = self.format_om(om)
            df = self.read_prize_pool()
            bal = self.get_balance(om_new)
            red = self.get_redeemed(om_new) if not cfg.view_only else 0
            avail = max(0, bal - red)

            cards = []
            for i in df.index:
                row = df.loc[i]
                out_of_bal = row["cost"] > avail
                no_stock = row["inventory"] == 0
                card = self._build_item_card(i, row)
                if no_stock or out_of_bal:
                    card.style = {"display": "none"}
                cards.append(card)
            return cards

        # ---- 2. Player validation + store hydration on Check ----------
        @callback(
            Output(id_("visible-rows"), "data"),
            Output(id_("item-limit-store"), "data"),
            Output(id_("token"), "data"),
            Output(id_("red"), "data"),
            Output(id_("initials-textbox"), "value"),
            Output(id_("tier-textbox"), "value"),
            Output(id_("items-grid"), "className"),
            Output(id_("Error-text"), "children"),
            Output(id_("credits-section"), "style"),
            Output(id_("main-container-items"), "style"),
            Output(id_("logo-main"), "style"),
            Output(id_("prev-redeemed-by-cat"), "data"),
            *([Output(id_("redeem-footer"), "className"),
               Output(id_("redeem-footer"), "style")] if not cfg.view_only else []),
            Input(id_("export-button"), "n_clicks"),
            State(id_("uid-textbox"), "value"),
            prevent_initial_call=True,
        )
        def validate_player(n_clicks, om_number):
            HIDDEN_GRID = f"shop-items-grid columns is-hidden"
            STYLE_HIDDEN = {"display": "none"}
            NO_CHANGE = dash.no_update

            extra_hidden = (f"shop-redeem-footer footer is-hidden", STYLE_HIDDEN) if not cfg.view_only else ()
            extra_shown = (f"shop-redeem-footer footer is-fixed-bottom has-text-centered", {"display": "block"}) if not cfg.view_only else ()

            def _reject(error_msg, initials="", tier=""):
                base = ([], 0, NO_CHANGE, NO_CHANGE, initials, tier,
                         HIDDEN_GRID, error_msg, STYLE_HIDDEN, NO_CHANGE, NO_CHANGE, {})
                return base + extra_hidden

            if not om_number:
                return _reject("❌ Please enter a valid OM Number.")

            om = self.format_om(om_number)

            try:
                initials = self.find_initials(om)
            except Exception:
                initials = "Not found"

            tier = self.get_tier(om)
            if tier == "NA":
                return _reject("❌ Patron is not Qualified", initials=initials, tier=tier)

            balance = self.get_balance(om)
            if balance < 1:
                return _reject("❌ No earning for this OM.", initials=initials, tier=tier)

            redeemed = self.get_redeemed(om) if not cfg.view_only else 0
            total_balance = max(0, balance - redeemed)

            df = self.read_prize_pool()
            df_local = df[(df["inventory"] > 0) & (df["cost"] <= total_balance)].copy()
            visible_idxs = df_local.index.tolist()
            prev_cat_counts = self.get_redeemed_per_category(om, df) if not cfg.view_only else {}

            result = (
                visible_idxs, total_balance, balance, redeemed, initials, tier,
                f"shop-items-grid columns is-multiline", "", {"display": "block"},
                {"transition": "all 0.3s ease-in-out", "paddingTop": "0vh"},
                {"display": "none"}, prev_cat_counts,
            )
            return result + extra_shown

        # ---- 3. TP display boxes ---------------------------------------
        @callback(
            Output(id_("tp-display"), "value"),
            Output(id_("tp-redeem"), "value"),
            Output(id_("tp-balance"), "value"),
            Input(id_("token"), "data"),
            State(id_("red"), "data"),
        )
        def update_tp_display(token, red):
            try:
                token_val = float(token) if token is not None else 0
                balance = max(token_val - (red or 0), 0)
                return token, red, balance
            except (TypeError, ValueError):
                return 0, 0, 0

        # ---- 4. Page refresh --------------------------------------------
        refresh_inputs = [Input(id_("back-button"), "n_clicks")]
        if not cfg.view_only:
            refresh_inputs.insert(0, Input(id_("confirm-redeem-button"), "n_clicks"))

        @callback(
            Output(id_("url"), "href"),
            *refresh_inputs,
            prevent_initial_call=True,
        )
        def page_refresh(*_clicks):
            trigger_id = ctx.triggered_id
            if trigger_id == id_("confirm-redeem-button"):
                time_module.sleep(3)
                return cfg.page_path
            if trigger_id == id_("back-button"):
                return cfg.page_path
            return dash.no_update

        # ---- 5. Modal open/close ----------------------------------------
        @callback(
            Output(id_("selected-item-id"), "data"),
            Output(id_("item-description"), "className"),
            Input(wid("card", ALL), "n_clicks"),
            Input(id_("close-button"), "n_clicks"),
            *([Input(id_("item-add"), "n_clicks")] if not cfg.view_only else []),
            prevent_initial_call=True,
        )
        def manage_item_modal(card_clicks, close_clicks, *maybe_add):
            triggered = ctx.triggered_id

            if triggered is None:
                raise PreventUpdate

            if isinstance(triggered, str):
                if triggered == id_("close-button"):
                    return None, "modal"

                if not cfg.view_only and triggered == id_("item-add"):
                    return None, "modal"

                raise PreventUpdate

            if hasattr(triggered, "get"):
                if triggered.get("type") == f"card-{self.suffix}":
                    idx = int(triggered.get("index", -1))

                    if (
                        card_clicks
                        and 0 <= idx < len(card_clicks)
                        and card_clicks[idx]
                    ):
                        return idx, "modal is-active"

            raise PreventUpdate

        # ---- 6a. Load modal content -------------------------------------
        @callback(
            Output(id_("item-image"), "src"),
            Output(id_("item-name"), "children"),
            Output(id_("item-cost"), "children"),
            Output(id_("modal-item-index"), "data"),
            Output(id_("qty"), "children"),
            Output(id_("current-quantity"), "data"),
            Output(id_("category-limit-warning"), "children"),
            Input(id_("selected-item-id"), "data"),
            State(id_("quantities-store"), "data") if not cfg.view_only else State(id_("modal-item-index"), "data"),
            State(id_("prev-redeemed-by-cat"), "data"),
            prevent_initial_call=True,
        )
        def load_modal_content(selected_idx, quantities, prev_cat_counts):
            if selected_idx is None:
                raise PreventUpdate
            try:
                idx = int(selected_idx)
            except (TypeError, ValueError):
                raise PreventUpdate

            df = self.read_prize_pool()
            if idx not in df.index:
                raise PreventUpdate

            quantities = quantities if (not cfg.view_only and quantities) else {}
            prev_cat_counts = prev_cat_counts or {}

            qty = int(quantities.get(str(idx), 0)) if not cfg.view_only else 0
            category = str(df.at[idx, "category"]).strip()
            warning = self._category_warning(category, prev_cat_counts)

            return (
                f"/assets/inventory/{cfg.assets_folder}/{df.loc[idx, 'ID']}.png",
                df.loc[idx, "name"],
                f"{df.loc[idx, 'cost']} {cfg.currency_label}",
                idx, qty, qty, warning,
            )

        if cfg.view_only:
            return  # Everything below is cart/redeem logic — view-only stops here.

        # ---- 6b. Quantity controls (+/-) --------------------------------
        @callback(
            Output(id_("qty"), "children", allow_duplicate=True),
            Output(id_("current-quantity"), "data", allow_duplicate=True),
            Output(id_("category-limit-warning"), "children", allow_duplicate=True),
            Input(id_("add-button"), "n_clicks"),
            Input(id_("sub-button"), "n_clicks"),
            State(id_("current-quantity"), "data"),
            State(id_("modal-item-index"), "data"),
            State(id_("quantities-store"), "data"),
            State(id_("item-limit-store"), "data"),
            State(id_("prev-redeemed-by-cat"), "data"),
            prevent_initial_call=True,
        )
        def update_quantity(add_clicks, sub_clicks, curr_qty, curr_idx, quantities, lim, prev_cat_counts):
            triggered = ctx.triggered_id
            if triggered not in (id_("add-button"), id_("sub-button")):
                raise PreventUpdate
            if curr_idx is None:
                raise PreventUpdate

            try:
                curr_idx = int(curr_idx)
            except (TypeError, ValueError):
                raise PreventUpdate

            df = self.read_prize_pool()
            if curr_idx not in df.index:
                raise PreventUpdate

            df["category"] = df["category"].astype(str).str.strip()
            category = df.at[curr_idx, "category"]
            cost = float(df.at[curr_idx, "cost"])
            inv = int(df.at[curr_idx, "inventory"])
            curr_qty = int(curr_qty or 0)
            quantities = quantities or {}
            prev_cat_counts = prev_cat_counts or {}
            lim = lim or 0

            parsed_q: Dict[int, int] = {}
            for k, v in quantities.items():
                try:
                    parsed_q[int(k)] = int(v or 0)
                except Exception:
                    continue

            total_cost_excl = sum(
                float(df.at[i, "cost"]) * q for i, q in parsed_q.items() if i != curr_idx
            )
            cart_cat_excl = sum(
                q for i, q in parsed_q.items()
                if i != curr_idx and df.at[i, "category"] == category
            )
            prev_redeemed_cat = int(prev_cat_counts.get(category, 0))

            new_qty = curr_qty
            if triggered == id_("add-button"):
                proposed_qty = curr_qty + 1
                total_cat_used = prev_redeemed_cat + cart_cat_excl + proposed_qty
                if (
                    proposed_qty <= inv
                    and (total_cost_excl + proposed_qty * cost) <= lim
                    and total_cat_used <= cfg.max_per_category
                ):
                    new_qty = proposed_qty
            else:
                new_qty = max(0, curr_qty - 1)

            return new_qty, new_qty, self._category_warning(category, prev_cat_counts)

        # ---- 7. Cart store + total value --------------------------------
        @callback(
            Output(id_("quantities-store"), "data"),
            Output(id_("total-value"), "children"),
            Output(id_("cart-value"), "data"),
            Input(id_("item-add"), "n_clicks"),
            Input(id_("export-button"), "n_clicks"),
            State(id_("modal-item-index"), "data"),
            State(id_("current-quantity"), "data"),
            State(id_("quantities-store"), "data"),
            prevent_initial_call=True,
        )
        def update_cart(add_click, exp, curr_idx, curr_qty, quantities):
            triggered = callback_context.triggered[0]["prop_id"].split(".")[0] if callback_context.triggered else None
            if not triggered or curr_idx is None:
                raise PreventUpdate

            if triggered == id_("export-button"):
                return {}, 0, 0

            df = self.read_prize_pool()
            quantities = quantities or {}
            key = str(curr_idx)

            if curr_qty == 0:
                quantities.pop(key, None)
            else:
                quantities[key] = curr_qty

            total = self.calculate_total_value(quantities, df)
            return quantities, total, total

        # ---- 8. Quantity badges on grid cards (clientside) --------------
        clientside_callback(
            """
            function(quantities, visible_indices, df_length) {
                var out = [];
                for (var i = 0; i < df_length; i++) {
                    var idx = String(i);
                    out.push((quantities && quantities.hasOwnProperty(idx)) ? quantities[idx] : 0);
                }
                return out;
            }
            """,
            Output(wid("item-qty", ALL), "children"),
            Input(id_("quantities-store"), "data"),
            Input(id_("visible-rows"), "data"),
            State(id_("df-length"), "data"),
        )

        # ---- 9. Redeem modal + confirmation flow ------------------------
        @callback(
            Output(id_("redeem-modal"), "style"),
            Output(id_("modal-basket-content"), "children"),
            Output(id_("redeem-status"), "children"),
            Output(id_("uid-textbox"), "value"),
            Output(id_("interval-refresh"), "disabled"),
            Output(id_("confirm-redeem-button"), "disabled"),
            Output(id_("last-confirm-ts"), "data"),
            Input(id_("redeem-button"), "n_clicks"),
            Input(id_("cancel-redeem-button"), "n_clicks"),
            Input(id_("cancel-redeem-button2"), "n_clicks"),
            Input(id_("confirm-redeem-button"), "n_clicks"),
            State(id_("token"), "data"),
            State(id_("quantities-store"), "data"),
            State(id_("uid-textbox"), "value"),
            State(id_("last-confirm-ts"), "data"),
            prevent_initial_call=True,
        )
        def handle_redeem_modal(redeem_click, cancel_click, cancel_click2, confirm_click,
                                 credits_balance, quantities, om_number, last_ts):
            button_id = ctx.triggered_id
            now_ms = int(datetime.now().timestamp() * 1000)
            NO_UP = dash.no_update

            MODAL_STYLE_VISIBLE = {
                "display": "flex", "position": "fixed",
                "top": 0, "left": 0, "right": 0, "bottom": 0,
                "backgroundColor": "rgba(0,0,0,0.6)",
                "justifyContent": "center", "alignItems": "center",
                "zIndex": 1000,
            }
            MODAL_HIDDEN = {"display": "none"}

            om = self.format_om(om_number)
            df = self.read_prize_pool()

            if button_id == id_("redeem-button"):
                if quantities:
                    basket_rows, total = [], 0
                    for idx_str, qty in quantities.items():
                        if qty <= 0:
                            continue
                        idx = int(idx_str)
                        name = df.loc[idx, "name"]
                        price = df.loc[idx, "cost"]
                        total += price * qty
                        basket_rows.append(f"{name} (x{qty}) — {price * qty} pts")
                    basket_rows.append(f"Total: {total} pts")
                    content = html.Ul([html.Li(r) for r in basket_rows])
                else:
                    content = "No items selected."
                return MODAL_STYLE_VISIBLE, content, NO_UP, NO_UP, NO_UP, False, NO_UP

            if button_id in (id_("cancel-redeem-button"), id_("cancel-redeem-button2")):
                return MODAL_HIDDEN, NO_UP, NO_UP, NO_UP, NO_UP, False, NO_UP

            if button_id == id_("confirm-redeem-button"):
                if now_ms - (last_ts or 0) < 1500:
                    self.logger.warning(f"Duplicate confirm click ignored for {om_number}")
                    return NO_UP, NO_UP, NO_UP, NO_UP, NO_UP, True, NO_UP

                if not quantities:
                    return MODAL_HIDDEN, NO_UP, "No items selected to redeem.", NO_UP, False, True, NO_UP

                try:
                    shop = self._shop_transaction()
                    inventory = self._inventory()

                    insufficient, order_items, total_val = [], [], 0
                    self.logger.info(f"{om} cart: {quantities}")

                    for idx_str, qty in quantities.items():
                        if qty == 0:
                            continue
                        idx = int(idx_str)
                        item_name = df.loc[idx, "name"]
                        price = int(df.loc[idx, "cost"])
                        stock_row = inventory.get_item_by_name(item_name)

                        if not stock_row:
                            insufficient.append(f"{item_name} (Not found)")
                            continue

                        if qty > stock_row["inventory"]:
                            insufficient.append(f"{item_name} (Only {stock_row['inventory']} left)")
                        else:
                            order_items.append({
                                "item": item_name, "quantity": qty, "unit_points": price,
                                "total": qty * price, "item_id": stock_row["id"],
                            })
                            total_val += qty * price

                    if insufficient:
                        return (
                            MODAL_HIDDEN, NO_UP,
                            html.Div([
                                html.Span("Redemption failed. Insufficient stock: ", style={"color": "red"}),
                                html.Ul([html.Li(i) for i in insufficient]),
                            ]),
                            NO_UP, NO_UP, True, NO_UP,
                        )

                    redeemed = shop.get_total_redeemed(om)
                    effective_credits = max(0, int(credits_balance or 0) - redeemed)
                    allocated = self.allocate_payment(order_items, effective_credits, 0)

                    for item in allocated:
                        result = shop.add_transaction(
                            uid=om, item_id=item["item_id"], item_name=item["item"],
                            quantity=item["quantity"], cost=item["unit_points"],
                            total_val=item["total"], credits_used=item["credits_used"],
                            cp_used=item["cp_used"], status="pending",
                        )
                        self.logger.info(f"Transaction pushed: {item['item_id']} x{item['quantity']} -> {result is True}")

                        if result is True:
                            try:
                                inv_result = inventory.subtract_quantity(item["item_id"], item["quantity"])
                                if inv_result is True:
                                    self.logger.info(f"Inventory updated: -{item['quantity']} from {item['item_id']}")
                                else:
                                    self.logger.warning(f"Inventory issue for {item['item_id']}: {inv_result}")
                            except Exception as e:
                                self.logger.error(f"Inventory error for {item['item_id']}: {e}")
                        else:
                            self.logger.error(f"Failed to process {item['item']} for {om}: {result}")
                            return (
                                MODAL_HIDDEN, NO_UP,
                                html.Span(f"Redemption failed: {result}", style={"color": "red"}),
                                NO_UP, NO_UP, True, NO_UP,
                            )

                    self.logger.info(f"{om} redemption successful: {order_items}")
                    return (
                        MODAL_HIDDEN, NO_UP,
                        html.Span("Items successfully redeemed!", style={"color": "green"}),
                        "", NO_UP, True, NO_UP,
                    )

                except Exception as e:
                    self.logger.error(f"{om} error: {e}")
                    return (
                        MODAL_HIDDEN, NO_UP,
                        html.Span(f"Error: {str(e)}", style={"color": "red"}),
                        NO_UP, NO_UP, True, NO_UP,
                    )

            return NO_UP, NO_UP, NO_UP, NO_UP, NO_UP, NO_UP, NO_UP