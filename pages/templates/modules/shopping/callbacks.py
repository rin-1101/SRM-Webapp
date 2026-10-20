"""Dash callback registration for shopping pages."""

import time as time_module
from datetime import datetime
from typing import Dict

import dash
from dash import (
    ALL,
    Input,
    Output,
    State,
    callback,
    clientside_callback,
    ctx,
    html,
)
from dash.exceptions import PreventUpdate


class ShopCallbacksMixin(object):
    def _register_callbacks(self) -> None:
        cfg = self.config
        id_ = self.id
        wid = self.wid

        def _resolve_callback_coding_tag(coding_context=None, om_number=None):
            tag = self._normalize_coding_tag(coding_context)
            if not cfg.bdcoding or not om_number:
                return tag

            current_om = self.format_om(om_number)
            stored_om = coding_context.get("om") if isinstance(coding_context, dict) else None
            if stored_om and self.format_om(stored_om) == current_om:
                return tag

            self.logger.info("Refreshing stale coding context | tag: %s | om: %s", tag, current_om)
            with self.loader_session() as loader:
                fresh_tag, _coding_display, _coding_source = self.get_coding_tag(
                    current_om, loader=loader
                )
            return self._normalize_coding_tag(fresh_tag) or tag

        def _build_basket_content(df, quantities):
            rows = []
            total = 0
            for idx_str, raw_qty in (quantities or {}).items():
                try:
                    idx = int(idx_str)
                    qty = int(raw_qty or 0)
                    if qty <= 0 or idx not in df.index:
                        continue
                    name = df.loc[idx, "name"]
                    price = df.loc[idx, "cost"]
                except (TypeError, ValueError, KeyError):
                    continue

                line_total = price * qty
                total += line_total
                rows.append(html.Div(
                    className="shop-basket-row",
                    children=[
                        html.Div(
                            className="shop-basket-item-copy",
                            children=[
                                html.Strong(name),
                                html.Span("{} {} each".format(price, cfg.currency_label)),
                            ],
                        ),
                        html.Div(
                            className="shop-basket-row-actions",
                            children=[
                                html.Button(
                                    "-",
                                    id=wid("basket-decrease", idx),
                                    n_clicks=0,
                                    className="shop-basket-adjust",
                                    **{"aria-label": "Reduce {}".format(name)}
                                ),
                                html.Span(
                                    "Qty {}".format(qty),
                                    className="shop-basket-row-quantity",
                                ),
                                html.Button(
                                    "Remove",
                                    id=wid("basket-remove", idx),
                                    n_clicks=0,
                                    className="shop-basket-remove",
                                ),
                            ],
                        ),
                        html.Strong(
                            "{} {}".format(line_total, cfg.currency_label),
                            className="shop-basket-line-total",
                        ),
                    ],
                ))

            if not rows:
                return html.Div(
                    "No items selected.",
                    className="shop-empty-basket",
                )

            return html.Div(children=[
                html.Div(rows, className="shop-basket-rows"),
                html.Div(
                    className="shop-basket-modal-total",
                    children=[
                        html.Span("TOTAL"),
                        html.Strong("{} {}".format(total, cfg.currency_label)),
                    ],
                ),
            ])

        if len(cfg.style_options) > 1:
            @callback(
                Output(id_("main-container"), "className"),
                Input(id_("style-selector"), "value"),
                Input(id_("coding-tag"), "data"),
            )
            def switch_shop_style(selected_style, coding_tag):
                allowed = set(option["value"] for option in cfg.style_options)
                style_name = selected_style if selected_style in allowed else cfg.default_style
                container_class = (
                    "shop-main-container shop-tablet-commerce "
                    "shop-theme-{}".format(style_name)
                )
                if cfg.low_power_mode:
                    container_class += " shop-low-power"
                return container_class

        # ---- 1. Validate player, hydrate stores, and build item grid ----
        @callback(
            Output(id_("visible-rows"), "data"),
            Output(id_("items-grid"), "children"),
            Output(id_("item-limit-store"), "data"),
            Output(id_("token"), "data"),
            Output(id_("red"), "data"),
            Output(id_("initials-textbox"), "value"),
            Output(id_("tier-textbox"), "value"),
            *([Output(id_("tagging-textbox"), "value")] if cfg.bdcoding else []),
            Output(id_("coding-tag"), "data"),
            Output(id_("items-grid"), "className"),
            Output(id_("Error-text"), "children"),
            Output(id_("credits-section"), "style"),
            Output(id_("main-container-items"), "style"),
            Output(id_("logo-main"), "style"),
            Output(id_("prev-redeemed-by-cat"), "data"),
            Output(id_("df-length"), "data"),
            Output(id_("category-filter"), "options"),
            Output(id_("category-filter"), "value"),
            Output(id_("main-container"), "style"),
            *([Output(id_("redeem-footer"), "className"),
               Output(id_("redeem-footer"), "style")] if not cfg.view_only else []),
            Input(id_("export-button"), "n_clicks"),
            State(id_("uid-textbox"), "value"),
            prevent_initial_call=True,
        )
        def validate_player(n_clicks, om_number):
            HIDDEN_GRID = "shop-items-grid columns is-hidden"
            STYLE_HIDDEN = {"display": "none"}
            NO_CHANGE = dash.no_update

            extra_hidden = ("shop-redeem-footer is-hidden", STYLE_HIDDEN) if not cfg.view_only else ()
            extra_shown = ("shop-redeem-footer", {"display": "flex"}) if not cfg.view_only else ()

            def _reject(error_msg, initials="", tier="", tagging="", coding_context=None):
                tagging_output = (tagging,) if cfg.bdcoding else ()
                base = (([], [], 0, NO_CHANGE, NO_CHANGE, initials, tier) + tagging_output +
                        (coding_context, HIDDEN_GRID, error_msg, STYLE_HIDDEN, NO_CHANGE,
                         NO_CHANGE, {}, 0,
                         [{"label": "ALL", "value": "all"}], "all", NO_CHANGE))
                return base + extra_hidden

            if not n_clicks or not om_number:
                return _reject("Please enter a valid OM Number.")

            if not self.is_valid_om(om_number):
                return _reject("OM Number must contain digits only.")

            om = self.format_om(om_number)
            test_profile = cfg.test_profiles.get(om)
            entitlement_override = self.get_entitlement_override(om)
            if test_profile:
                initials = test_profile.get("initials", "T.A.")
                tier = test_profile.get("tier", "Test Account")
                coding_tag, coding_display, coding_source = self.get_coding_tag(om)
                balance = self.get_balance(om)
            elif entitlement_override:
                initials = "Override"
                tier = "Entitled"
                coding_tag, coding_display, coding_source = self.get_coding_tag(om)
                balance = self.get_balance(om)
            else:
                with self.loader_session() as loader:
                    try:
                        initials = self.find_initials(om, loader=loader)
                    except Exception:
                        initials = "Not found"

                    tier = self.get_tier(om, loader=loader)
                    if tier == "NA":
                        return _reject(
                            "Patron is not Qualified",
                            initials=initials,
                            tier=tier,
                        )

                    coding_tag, coding_display, coding_source = self.get_coding_tag(
                        om, loader=loader
                    )
                    balance = self.get_balance(om, loader=loader)

            coding_context = {"om": om, "tag": coding_tag}
            if cfg.bdcoding and not coding_tag:
                return _reject(
                    "Patron is not entitled.",
                    initials=initials,
                    tier=tier,
                    tagging=coding_display,
                    coding_context=coding_context,
                )
            coding_debug = ""

            if balance < 1:
                return _reject(
                    "No earning for this OM.",
                    initials=initials,
                    tier=tier,
                    tagging=coding_display,
                    coding_context=coding_context,
                )

            df = self.read_prize_pool(coding_tag)
            redeemed, prev_cat_counts = self.get_redemption_summary(om, df)
            total_balance = max(0, balance - redeemed)

            df_local = df[(df["inventory"] > 0) & (df["cost"] <= total_balance)].copy()
            visible_idxs = df_local.index.tolist()
            unlimited_redemptions = self.has_unlimited_redemptions(om)
            redemption_limit_reached = (
                not unlimited_redemptions
                and not self._within_redemption_limit(prev_cat_counts, 1, om)
            )
            cards = [
                self._build_item_card(
                    i, df.loc[i], coding_tag,
                    unavailable=redemption_limit_reached,
                )
                for i in visible_idxs
            ]

            category_options = [{"label": "ALL", "value": "all"}]
            seen_categories = set()
            for raw_category in df_local["category"].tolist():
                label = str(raw_category or "").strip()
                value = self.category_slug(label)
                if not label or label.casefold() == "nan" or value in seen_categories:
                    continue
                seen_categories.add(value)
                category_options.append({"label": label.upper(), "value": value})

            tagging_output = (coding_display,) if cfg.bdcoding else ()
            result = (
                (visible_idxs, cards, total_balance, balance, redeemed, initials, tier) + tagging_output +
                (coding_context, "shop-items-grid", coding_debug, {"display": "block"},
                 {"transition": "all 0.3s ease-in-out"},
                 {"display": "none"}, prev_cat_counts, len(df.index),
                 category_options, "all", self.get_background_style_for_tag())
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

                    # Pattern-match click lists are positional, while idx is the
                    # prize-pool database index and may be non-contiguous.
                    if card_clicks and any(card_clicks):
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
            State(id_("coding-tag"), "data"),
            State(id_("uid-textbox"), "value"),
            prevent_initial_call=True,
        )
        def load_modal_content(selected_idx, quantities, prev_cat_counts, coding_tag, om_number):
            if selected_idx is None:
                raise PreventUpdate
            try:
                idx = int(selected_idx)
            except (TypeError, ValueError):
                raise PreventUpdate

            coding_tag = _resolve_callback_coding_tag(coding_tag, om_number)
            df = self.read_prize_pool(coding_tag)
            if idx not in df.index:
                raise PreventUpdate

            quantities = quantities if (not cfg.view_only and quantities) else {}
            prev_cat_counts = prev_cat_counts or {}

            qty = int(quantities.get(str(idx), 0)) if not cfg.view_only else 0
            category = str(df.at[idx, "category"]).strip()
            warning = (
                ""
                if self.has_unlimited_redemptions(om_number)
                else self._redemption_warning(prev_cat_counts, om_number)
                    or self._category_warning(category, prev_cat_counts, om_number)
            )
            assetspath = f"/assets/inventory/{cfg.assets_folder}/{df.loc[idx, 'ID']}.png"
            # assetspath = f"/assets/inventory/{cfg.assets_folder}/{coding_tag}/{df.loc[idx, 'ID']}.png"
            if(coding_tag and coding_tag != "DEFAULT"):
                assetspath = f"/assets/inventory/{cfg.assets_folder}/{coding_tag}/{df.loc[idx, 'ID']}.png"
            # if not self.asset_exists(assetspath):
            #     assetspath = f"/assets/DEFAULT/okada-long.png"
            return (
                assetspath,
                df.loc[idx, "name"],
                f"{df.loc[idx, 'cost']} {cfg.currency_label}",
                idx, qty, qty, warning,
            )

        # ---- 6b. Client-side catalogue category/search filters ---------
        clientside_callback(
            """
            function(category, searchText, itemIds) {
                var selected = category || "all";
                var needle = String(searchText || "")
                    .toLowerCase()
                    .replace(/[^a-z0-9]+/g, "-")
                    .replace(/^-+|-+$/g, "");
                return (itemIds || []).map(function(itemId) {
                    var parts = String((itemId || {}).index || "").split("|");
                    var categorySlug = parts[0] || "uncategorized";
                    var nameSlug = parts[1] || "";
                    var categoryMatches = selected === "all" || categorySlug === selected;
                    var searchMatches = !needle || nameSlug.indexOf(needle) !== -1;
                    return categoryMatches && searchMatches ? {} : {"display": "none"};
                });
            }
            """,
            Output(wid("catalog-item", ALL), "style"),
            Input(id_("category-filter"), "value"),
            Input(id_("catalog-search"), "value"),
            State(wid("catalog-item", ALL), "id"),
        )

        if cfg.view_only:
            return  # Everything below is cart/redeem logic ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â view-only stops here.

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
            State(id_("coding-tag"), "data"),
            State(id_("uid-textbox"), "value"),
            prevent_initial_call=True,
        )
        def update_quantity(add_clicks, sub_clicks, curr_qty, curr_idx, quantities, lim, prev_cat_counts, coding_tag, om_number):
            triggered = ctx.triggered_id
            if triggered not in (id_("add-button"), id_("sub-button")):
                raise PreventUpdate
            if curr_idx is None:
                raise PreventUpdate

            try:
                curr_idx = int(curr_idx)
            except (TypeError, ValueError):
                raise PreventUpdate

            coding_tag = _resolve_callback_coding_tag(coding_tag, om_number)
            df = self.read_prize_pool(coding_tag)
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
            cart_qty_excl = sum(
                max(0, q) for i, q in parsed_q.items() if i != curr_idx
            )
            prev_redeemed_cat = int(prev_cat_counts.get(category, 0))
            unlimited_redemptions = self.has_unlimited_redemptions(om_number)
            category_limit = self.get_category_limit(om_number)

            new_qty = curr_qty
            if triggered == id_("add-button"):
                proposed_qty = curr_qty + 1
                total_cat_used = prev_redeemed_cat + cart_cat_excl + proposed_qty
                if (
                    proposed_qty <= inv
                    and (total_cost_excl + proposed_qty * cost) <= lim
                    and (
                        unlimited_redemptions
                        or (
                            self._within_redemption_limit(
                                prev_cat_counts,
                                cart_qty_excl + proposed_qty,
                                om_number,
                            )
                            and total_cat_used <= category_limit
                        )
                    )
                ):
                    new_qty = proposed_qty
            else:
                new_qty = max(0, curr_qty - 1)

            warning = (
                ""
                if unlimited_redemptions
                else self._category_warning(category, prev_cat_counts, om_number)
            )
            return new_qty, new_qty, warning

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
            State(id_("coding-tag"), "data"),
            State(id_("uid-textbox"), "value"),
            prevent_initial_call=True,
        )
        def update_cart(add_click, exp, curr_idx, curr_qty, quantities, coding_tag, om_number):
            triggered = ctx.triggered_id
            if not triggered or curr_idx is None:
                raise PreventUpdate

            if triggered == id_("export-button"):
                return {}, 0, 0

            coding_tag = _resolve_callback_coding_tag(coding_tag, om_number)
            df = self.read_prize_pool(coding_tag)
            quantities = quantities or {}
            key = str(curr_idx)

            if curr_qty == 0:
                quantities.pop(key, None)
            else:
                quantities[key] = curr_qty

            total = self.calculate_total_value(quantities, df)
            return quantities, total, total

        # ---- 7b. Quick add from catalogue cards -------------------------
        if cfg.quick_add:
            @callback(
                Output(id_("quantities-store"), "data", allow_duplicate=True),
                Output(id_("total-value"), "children", allow_duplicate=True),
                Output(id_("cart-value"), "data", allow_duplicate=True),
                Input(wid("quick-add", ALL), "n_clicks"),
                State(id_("quantities-store"), "data"),
                State(id_("item-limit-store"), "data"),
                State(id_("prev-redeemed-by-cat"), "data"),
                State(id_("coding-tag"), "data"),
                State(id_("uid-textbox"), "value"),
                prevent_initial_call=True,
            )
            def quick_add_to_cart(clicks, quantities, limit, prev_cat_counts,
                                  coding_tag, om_number):
                triggered = ctx.triggered_id
                if (
                    not isinstance(triggered, dict)
                    or triggered.get("type") != "quick-add-{}".format(self.suffix)
                    or not any(clicks or [])
                ):
                    raise PreventUpdate

                try:
                    idx = int(triggered.get("index"))
                except (TypeError, ValueError):
                    raise PreventUpdate

                coding_tag = _resolve_callback_coding_tag(coding_tag, om_number)
                df = self.read_prize_pool(coding_tag)
                if idx not in df.index:
                    raise PreventUpdate

                df["category"] = df["category"].astype(str).str.strip()
                updated = dict(quantities or {})
                prev_cat_counts = prev_cat_counts or {}
                category = df.at[idx, "category"]
                current_qty = int(updated.get(str(idx), 0) or 0)
                inventory = int(df.at[idx, "inventory"])
                cost = float(df.at[idx, "cost"])
                current_total = self.calculate_total_value(updated, df)
                basket_quantity = sum(
                    max(0, int(raw_qty or 0))
                    for raw_qty in updated.values()
                )
                cart_category_qty = sum(
                    int(raw_qty or 0)
                    for raw_idx, raw_qty in updated.items()
                    if int(raw_idx) in df.index
                    and df.at[int(raw_idx), "category"] == category
                )
                previously_redeemed = int(prev_cat_counts.get(category, 0))
                unlimited_redemptions = self.has_unlimited_redemptions(om_number)
                category_limit = self.get_category_limit(om_number)

                if (
                    current_qty + 1 > inventory
                    or current_total + cost > (limit or 0)
                    or (
                        not unlimited_redemptions
                        and (
                            not self._within_redemption_limit(
                                prev_cat_counts, basket_quantity + 1, om_number
                            )
                            or previously_redeemed + cart_category_qty + 1
                                > category_limit
                        )
                    )
                ):
                    raise PreventUpdate

                updated[str(idx)] = current_qty + 1
                total = self.calculate_total_value(updated, df)
                return updated, total, total

            @callback(
                Output(wid("card", ALL), "className"),
                Output(wid("quick-add", ALL), "disabled"),
                Input(id_("quantities-store"), "data"),
                Input(id_("item-limit-store"), "data"),
                Input(id_("prev-redeemed-by-cat"), "data"),
                Input(id_("visible-rows"), "data"),
                State(id_("coding-tag"), "data"),
                State(id_("uid-textbox"), "value"),
            )
            def update_card_availability(quantities, limit, prev_cat_counts,
                                         visible_indices, coding_tag, om_number):
                visible_indices = visible_indices or []
                if not visible_indices:
                    return [], []

                coding_tag = _resolve_callback_coding_tag(coding_tag, om_number)
                df = self.read_prize_pool(coding_tag)
                df["category"] = df["category"].astype(str).str.strip()
                prev_cat_counts = prev_cat_counts or {}
                unlimited_redemptions = self.has_unlimited_redemptions(om_number)
                category_limit = self.get_category_limit(om_number)

                parsed_quantities = {}
                for raw_idx, raw_qty in (quantities or {}).items():
                    try:
                        parsed_quantities[int(raw_idx)] = int(raw_qty or 0)
                    except (TypeError, ValueError):
                        continue

                current_total = self.calculate_total_value(
                    {str(idx): qty for idx, qty in parsed_quantities.items()},
                    df,
                )
                basket_by_category = {}
                for idx, qty in parsed_quantities.items():
                    if idx not in df.index or qty <= 0:
                        continue
                    category = df.at[idx, "category"]
                    basket_by_category[category] = (
                        basket_by_category.get(category, 0) + qty
                    )

                basket_quantity = sum(
                    max(0, qty) for qty in parsed_quantities.values()
                )
                card_classes = []
                quick_add_disabled = []
                for raw_idx in visible_indices:
                    try:
                        idx = int(raw_idx)
                    except (TypeError, ValueError):
                        card_classes.append("shop-product-card is-unavailable")
                        quick_add_disabled.append(True)
                        continue

                    if idx not in df.index:
                        card_classes.append("shop-product-card is-unavailable")
                        quick_add_disabled.append(True)
                        continue

                    category = df.at[idx, "category"]
                    selected_qty = parsed_quantities.get(idx, 0)
                    inventory = int(df.at[idx, "inventory"])
                    cost = float(df.at[idx, "cost"])
                    category_used = (
                        int(prev_cat_counts.get(category, 0))
                        + basket_by_category.get(category, 0)
                    )
                    can_add = (
                        selected_qty + 1 <= inventory
                        and current_total + cost <= (limit or 0)
                        and (
                            unlimited_redemptions
                            or (
                                self._within_redemption_limit(
                                    prev_cat_counts,
                                    basket_quantity + 1,
                                    om_number,
                                )
                                and category_used + 1 <= category_limit
                            )
                        )
                    )

                    # Keep selected cards visually active even when another
                    # unit cannot be added; only unselected unavailable cards
                    # are grayed out.
                    card_classes.append(
                        "shop-product-card"
                        if can_add or selected_qty > 0
                        else "shop-product-card is-unavailable"
                    )
                    quick_add_disabled.append(not can_add)

                return card_classes, quick_add_disabled

        # ---- 8. Basket quantity adjustment ------------------------------
        @callback(
            Output(id_("quantities-store"), "data", allow_duplicate=True),
            Output(id_("total-value"), "children", allow_duplicate=True),
            Output(id_("cart-value"), "data", allow_duplicate=True),
            Output(id_("modal-basket-content"), "children", allow_duplicate=True),
            Input(wid("basket-decrease", ALL), "n_clicks"),
            Input(wid("basket-remove", ALL), "n_clicks"),
            State(id_("quantities-store"), "data"),
            State(id_("coding-tag"), "data"),
            State(id_("uid-textbox"), "value"),
            prevent_initial_call=True,
        )
        def adjust_basket(decrease_clicks, remove_clicks, quantities, coding_tag, om_number):
            triggered = ctx.triggered_id
            if not isinstance(triggered, dict):
                raise PreventUpdate

            component_type = triggered.get("type")
            if component_type not in (
                "basket-decrease-{}".format(self.suffix),
                "basket-remove-{}".format(self.suffix),
            ):
                raise PreventUpdate

            # Rendering the basket dynamically inserts these pattern-matched
            # buttons with n_clicks=0. Treat only an actual click as a basket
            # mutation; otherwise rebuilding the modal can decrement it again.
            triggered_clicks = (
                decrease_clicks
                if component_type == "basket-decrease-{}".format(self.suffix)
                else remove_clicks
            )
            if not any(triggered_clicks or []):
                raise PreventUpdate

            key = str(triggered.get("index"))
            updated = dict(quantities or {})
            current = int(updated.get(key, 0) or 0)
            if component_type == "basket-remove-{}".format(self.suffix):
                updated.pop(key, None)
            elif current <= 1:
                updated.pop(key, None)
            else:
                updated[key] = current - 1

            coding_tag = _resolve_callback_coding_tag(coding_tag, om_number)
            df = self.read_prize_pool(coding_tag)
            total = self.calculate_total_value(updated, df)
            return updated, total, total, _build_basket_content(df, updated)

        # ---- 9. Quantity badges on grid cards (clientside) --------------
        clientside_callback(
            """
            function(quantities, visible_indices) {
                return (visible_indices || []).map(function(i) {
                    var idx = String(i);
                    var quantity = (quantities && quantities.hasOwnProperty(idx)) ? quantities[idx] : 0;
                    return Number(quantity) > 0 ? quantity : "";
                });
            }
            """,
            Output(wid("item-qty", ALL), "children"),
            Input(id_("quantities-store"), "data"),
            Input(id_("visible-rows"), "data"),
        )

        # ---- 9. Basket item count (clientside) --------------------------
        clientside_callback(
            """
            function(quantities) {
                var total = Object.keys(quantities || {}).reduce(function(sum, key) {
                    return sum + (Number(quantities[key]) || 0);
                }, 0);
                return total + (total === 1 ? " ITEM" : " ITEMS");
            }
            """,
            Output(id_("cart-item-count"), "children"),
            Input(id_("quantities-store"), "data"),
        )

        # ---- 10. Redeem modal + confirmation flow -----------------------
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
            State(id_("coding-tag"), "data"),
            prevent_initial_call=True,
        )
        def handle_redeem_modal(redeem_click, cancel_click, cancel_click2, confirm_click,
                                 credits_balance, quantities, om_number, last_ts, coding_tag):
            button_id = ctx.triggered_id
            now_ms = int(datetime.now().timestamp() * 1000)
            NO_UP = dash.no_update

            MODAL_STYLE_VISIBLE = {
                "display": "flex", "position": "fixed",
                "top": 0, "left": 0, "right": 0, "bottom": 0,
                "backgroundColor": "rgba(0,0,0,0.6)",
                "justifyContent": "center", "alignItems": "flex-end",
                "zIndex": 1000,
            }
            MODAL_HIDDEN = {"display": "none"}

            om = self.format_om(om_number)
            coding_tag = _resolve_callback_coding_tag(coding_tag, om)
    
            df = self.read_prize_pool(coding_tag)

            if button_id == id_("redeem-button"):
                content = _build_basket_content(df, quantities)
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
                    inventory = self._inventory(coding_tag)

                    if not self.has_unlimited_redemptions(om):
                        current_cat_counts = self.get_redeemed_per_category(om, df)
                        requested_by_category = {}
                        for idx_str, qty in quantities.items():
                            requested_qty = max(0, int(qty or 0))
                            if requested_qty == 0:
                                continue
                            category = str(
                                df.at[int(idx_str), "category"]
                            ).strip()
                            requested_by_category[category] = (
                                requested_by_category.get(category, 0)
                                + requested_qty
                            )

                        requested_quantity = sum(requested_by_category.values())
                        if not self._within_redemption_limit(
                            current_cat_counts, requested_quantity, om
                        ):
                            return (
                                MODAL_HIDDEN, NO_UP,
                                html.Span(
                                    "Redemption failed. Maximum of {} item(s) "
                                    "allowed for this campaign.".format(
                                        self.get_redemption_limit(om)
                                    ),
                                    style={"color": "red"},
                                ),
                                NO_UP, NO_UP, True, NO_UP,
                            )

                        category_limit = self.get_category_limit(om)
                        category_limit_exceeded = any(
                            int(current_cat_counts.get(category, 0)) + quantity
                            > category_limit
                            for category, quantity
                            in requested_by_category.items()
                        )
                        if category_limit_exceeded:
                            return (
                                MODAL_HIDDEN, NO_UP,
                                html.Span(
                                    "Redemption failed. Maximum of {} item(s) "
                                    "allowed per category.".format(category_limit),
                                    style={"color": "red"},
                                ),
                                NO_UP, NO_UP, True, NO_UP,
                            )

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

                    redeemed = (
                        0
                        if self.has_unlimited_redemptions(om)
                        else shop.get_total_redeemed(om)
                    )
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
