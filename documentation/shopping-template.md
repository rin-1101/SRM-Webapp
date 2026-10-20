# Shopping Template

The shopping app is built around `pages/templates/shopping.py`. A campaign page should stay small: define paths, dates, style options, register the route, then hand a `ShopConfig` to `ShoppingPage`.

## Main Pieces

`ShopConfig` holds page-specific settings:

- Identity: `suffix`, `page_path`, `access_level`.
- Storage: `path_db`, `path_data`, `path_inv`, `path_tier_csv`, `db_filename`.
- Assets: `assets_folder`, `css_prefix`, `fallback_logo_src`.
- UI style selection: `style_options`, `default_style`.
- Campaign rules: `campaign_start`, `campaign_end`, redeemed window, valid tiers, category limits.
- Labels: TP field titles and search placeholder.
- Behavior: `view_only`, `background_mask`, logger name, QA balance overrides.

`ShoppingPage` owns the reusable behavior:

- Reads prize inventory from SQLite via `read_prize_pool()`.
- Gets player tier and TP balance.
- Builds item cards and the item-detail modal.
- Handles OM validation, cart quantity, category limits, and redeem confirmation callbacks.
- Adds the style picker when more than one `style_options` value is configured.

## Page Module Pattern

A new shopping page should follow this shape:

```python
from utils.paths import BDEAG
from utils.login_handler import require_login, restricted_page
from templates.shopping import ShopConfig, ShoppingPage

config = ShopConfig(
    suffix="bdeag",
    page_path=BDEAG,
    access_level=restricted_page[BDEAG]["access_level"],
    path_db=PATH_DB,
    path_data=PATH_DATA,
    path_inv=PATH_INV,
    path_tier_csv=PATH_TIER_CSV,
    db_filename="bdeag.db",
    assets_folder="shop",
    css_prefix="shop",
    style_options=("base", "minimalism", "liquid-glass"),
    default_style="base",
    campaign_start="2026-07-01 06:00:00",
    campaign_end="2026-07-31 05:59:00",
    redeemed_window_start="2026-07-01 06:00:00",
    redeemed_window_end="2026-07-31 06:00:00",
)

dash.register_page(__name__, path=config.page_path, name="BD Earn and Get")
require_login(__name__, access_level=config.access_level)

page = ShoppingPage(__name__, config)
layout = page.layout
page.register_callbacks()
```


## Logo Selection

`ShopConfig.logo` controls the main page logo loaded from the configured `assets_folder`.

```python
logo="default"  # /assets/<assets_folder>/logo.png
logo="cream"    # /assets/<assets_folder>/logo-cream.png
logo="bdeag"    # /assets/<assets_folder>/logo-bdeag.png
```

Rules:

- `default`, `logo`, or `logo.png` resolves to `logo.png`.
- `cream`, `logo-cream`, or `logo-cream.png` resolves to `logo-cream.png`.
- Any other value resolves to `logo-<value>.png`, unless it already ends with `.png`.

Use event-specific files such as `logo-bdeag.png` when one shared asset folder contains several event logos.
## Required Setup For A New Campaign

1. Add a route constant in `utils/paths.py`.

```python
BDEAG = "/bd-earn-and-get"
```

2. Add the page to `config/pages.yaml`.

```yaml
/bd-earn-and-get:
  name: BD Earn and Get
  access_role_group: shop
```

3. Create the page module in `pages/`.

Use a short, unique `suffix`. This suffix namespaces Dash component IDs so multiple shopping pages can coexist safely.

4. Prepare inventory data.

The template expects a SQLite database with a prize table, usually `prize_pool`, and item images named by item ID under:

```text
assets/inventory/<assets_folder>/<ID>.png
```

When using the shared `assets_folder="shop"`, the app uses shared page-level assets from:

```text
assets/shop/logo.png
assets/shop/bg.png
assets/shop/style.css
```

5. Keep campaign date values explicit.

Use full timestamps in `YYYY-MM-DD HH:MM:SS` format. The template uses `campaign_start` and `campaign_end` for TP earning, and the redeemed window for per-category redemption limits.

## View-Only Mode

Set `view_only=True` for catalogue-style pages. This keeps browsing and item details, but removes cart and redeem controls.

## QA Test Accounts

Use `balance_overrides` to set earned TP for a particular account. Add the same account to `test_profiles` when it needs a local identity that bypasses the live member/tier lookup:

```python
balance_overrides={"OM000000001": 50000},
test_profiles={"OM000000001": {"initials": "T.A.", "tier": "Test Account"}},
```

On Mickey, enter `1` in the numeric OM field; it normalizes to `OM000000001`. The account receives 50,000 earned TP. Available TP still subtracts existing redemptions, and normal category limits apply. Test profiles use the campaign's configured inventory and transaction storage. Other accounts retain the live lookup, and other campaigns have no test profiles unless explicitly configured.

## Access Control

Call `dash.register_page()` before `require_login()`. `require_login()` reads the registered page path and applies the configured role access from `config/pages.yaml`.

## When To Edit The Template

Edit `pages/templates/shopping.py` only for shared behavior that every shopping campaign should inherit. For campaign-specific settings, prefer changing the page module or adding a CSS theme under `assets/shop/styles/`.
