"""Configuration for reusable shopping pages."""

import re

class ShopConfig(object):
    """
    Everything that differs between shop instances lives here.
    A concrete page (e.g. `fire-horse.py`) builds one of these and
    hands it to `ShoppingPage`; nothing else needs to change.

    Plain class (not @dataclass) for compatibility with Python 3.6,
    where `dataclasses` isn't in the standard library.
    """

    @staticmethod
    def _normalize_style_name(style):
        name = str(style or "base").strip().lower().replace("_", "-")
        name = re.sub(r"[^a-z0-9-]+", "-", name).strip("-")
        return name or "base"

    @staticmethod
    def _normalize_tag_name(tag):
        return str(tag or "").strip().casefold().replace("_", "-")

    @classmethod
    def _normalize_tag_mapping(cls, mapping):
        return {
            cls._normalize_tag_name(key): value
            for key, value in dict(mapping or {}).items()
            if cls._normalize_tag_name(key)
        }

    @classmethod
    def _style_label(cls, style):
        return cls._normalize_style_name(style).replace("-", " ").title()

    @classmethod
    def _normalize_style_options(cls, style_options):
        if not style_options:
            style_options = ("base",)

        normalized = []
        seen = set()
        for option in style_options:
            if isinstance(option, dict):
                value = cls._normalize_style_name(option.get("value") or option.get("label"))
                label = option.get("label") or cls._style_label(value)
            else:
                value = cls._normalize_style_name(option)
                label = cls._style_label(value)

            if value not in seen:
                normalized.append({"label": label, "value": value})
                seen.add(value)

        return normalized or [{"label": "Base", "value": "base"}]
    @staticmethod
    def _resolve_logo_filename(logo):
        value = str(logo or "default").strip().lower()
        if value in ("default", "logo", "logo.png"):
            return "logo.png"
        if value in ("cream", "logo-cream", "logo-cream.png"):
            return "logo-cream.png"
        if value.endswith(".png"):
            return value
        if value.startswith("logo-"):
            return f"{value}.png"
        return f"logo-{value}.png"

    def __init__(
        self,
        # --- identity / routing -------------------------------------
        suffix,                       # e.g. "afhc", "afhc-view" Ã¢â‚¬â€ namespaces every ID
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
        logo="default",              # default -> logo.png, cream -> logo-cream.png, bdeag -> logo-bdeag.png
        css_prefix=None,              # CSS class prefix, e.g. "afhc" -> "afhc-card".
                                       # Defaults to `assets_folder` so an existing
                                       # per-shop stylesheet keeps working unmodified;
                                       # override explicitly if you want "shop-*"
                                       # classes shared across a common shop.css.
        style_options=None,           # selectable visual themes, e.g. ("base", "minimalism")
        default_style="base",
        # --- campaign rules ----------------------------------------------
        max_per_category=3,
        campaign_start="",            # "YYYY-MM-DD HH:MM:SS", TierPoint earn window
        campaign_end="",
        redeemed_window_start="",     # window used for per-category redeemed counts
        redeemed_window_end="",
        valid_tier_ids=(7, 15, 10022),
        allow_all_tiers=False,
        tier_names=None,              # default set below; avoids mutable-default trap
        # --- copy / labels (override per-shop without touching layout code) -
        currency_label="TP",
        search_placeholder="Enter OM Number",
        page_title_earned="TP Earned",
        page_title_redeemed="TP Redeemed",
        page_title_balance="TP Balance",
        member_title="Find your rewards",
        # --- behaviour ---------------------------------------------------
        view_only=False,              # True => no cart / redeem, browse only
        quick_add=False,              # True => direct Add to Cart controls on cards
        logger_name="shop-page",
        background_mask=None,         # optional overlay color for the page background
        bdcoding=False,               # True => resolve Patron coding/tagging and use tag-specific inventory
        bdcoding_tags=None,
        bdcoding_default_tag=None,
        bdcoding_entitlement_overrides=None,
        bdcoding_inventory_filenames=None,
        bdcoding_styles=None,
        bdcoding_backgrounds=None,
        bdcoding_masks=None,
        # --- dev / QA override: {om_number: forced_balance} -----------------
        balance_overrides=None,       # default set below; avoids mutable-default trap
        unlimited_redemption_uids=None,
        max_redemption=None,          # None => unlimited total item quantity
        low_power_mode=False,         # Reduce browser paint/image work for TV displays
        path_override=None,           # optional CSV: uid, redemptions, category, points, region
        test_profiles=None,           # opt-in QA identity: {uid: {initials, tier}}
    ):
        self.suffix = suffix
        self.page_path = page_path
        self.access_level = access_level

        self.path_db = path_db
        self.path_data = path_data
        self.path_inv = path_inv
        self.path_tier_csv = path_tier_csv
        self.path_override = path_override
        self.db_filename = db_filename
        self.orders_table = orders_table
        self.prize_table = prize_table

        self.assets_folder = assets_folder
        self.fallback_logo_src = fallback_logo_src
        self.logo = logo
        self.logo_filename = self._resolve_logo_filename(logo)
        self.css_prefix = css_prefix if css_prefix is not None else assets_folder
        self.style_options = self._normalize_style_options(style_options)
        self.default_style = self._normalize_style_name(default_style)
        if self.default_style not in [option["value"] for option in self.style_options]:
            self.style_options.insert(0, {
                "label": self._style_label(self.default_style),
                "value": self.default_style,
            })

        self.max_per_category = max_per_category
        if max_redemption is None:
            self.max_redemption = None
        else:
            self.max_redemption = int(max_redemption)
            if self.max_redemption < 1:
                raise ValueError("max_redemption must be at least 1 or None")
        self.campaign_start = campaign_start
        self.campaign_end = campaign_end
        self.redeemed_window_start = redeemed_window_start
        self.redeemed_window_end = redeemed_window_end
        self.valid_tier_ids = valid_tier_ids
        self.allow_all_tiers = bool(allow_all_tiers)
        self.tier_names = tier_names if tier_names is not None else {
            7: "Supreme", 15: "Maharlika", 10022: "Maharlika"
        }

        self.currency_label = currency_label
        self.search_placeholder = search_placeholder
        self.page_title_earned = page_title_earned
        self.page_title_redeemed = page_title_redeemed
        self.page_title_balance = page_title_balance
        self.member_title = member_title

        self.view_only = view_only
        self.quick_add = bool(quick_add)
        self.low_power_mode = bool(low_power_mode)
        self.logger_name = logger_name
        self.background_mask = background_mask
        self.bdcoding = bool(bdcoding)
        self.bdcoding_tags = tuple(
            self._normalize_tag_name(tag)
            for tag in (bdcoding_tags or ("local", "korea", "na", "sea", "japan"))
            if self._normalize_tag_name(tag)
        )
        self.bdcoding_default_tag = self._normalize_tag_name(bdcoding_default_tag) or None
        self.bdcoding_entitlement_overrides = {
            str(uid).strip().upper(): self._normalize_tag_name(tag)
            for uid, tag in dict(bdcoding_entitlement_overrides or {}).items()
            if (
                str(uid).strip()
                and self._normalize_tag_name(tag) in set(self.bdcoding_tags)
            )
        }
        self.bdcoding_inventory_filenames = self._normalize_tag_mapping(
            bdcoding_inventory_filenames
        )
        self.bdcoding_styles = self._normalize_tag_mapping(bdcoding_styles)
        self.bdcoding_backgrounds = self._normalize_tag_mapping(bdcoding_backgrounds)
        self.bdcoding_masks = self._normalize_tag_mapping(bdcoding_masks)

        self.balance_overrides = balance_overrides if balance_overrides is not None else {}
        self.test_profiles = {
            str(uid).strip().upper(): dict(profile)
            for uid, profile in dict(test_profiles or {}).items()
        }
        self.unlimited_redemption_uids = set(
            str(uid).strip().upper()
            for uid in (unlimited_redemption_uids or ())
            if str(uid).strip()
        )

        required = ["suffix", "page_path", "path_db", "path_data", "path_inv", "path_tier_csv"]
        missing = [name for name in required if not getattr(self, name)]
        if missing:
            raise ValueError("ShopConfig missing required field(s): {}".format(", ".join(missing)))


# ============================================================
#  Page
# ============================================================
