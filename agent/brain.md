# Agent Brain

This file is a persistent working memory for future tasks in this repository. Read this first before re-inspecting the same files.

## Repository context

- Workspace root: `l:/Strategic Marketing/Database Admin/ETL/Applications/reports`.
- Main app appears to be a Dash/Flask-style reporting app with pages under `pages/` and static assets under `assets/`.
- The shopping flow currently centers around:
  - `pages/templates/shopping.py` — reusable Dash shopping page template.
  - `pages/dyson-luxe.py` — Dyson Luxe Rewards page configuration.
  - `assets/shop.css` — shared generic shopping UI stylesheet.
  - `assets/dyson/style.css` — Dyson-specific theme overrides.

## Shopping template architecture

- `ShopConfig` in `pages/templates/shopping.py` owns per-shop configuration:
  - route/page path
  - storage paths
  - campaign windows
  - asset folder
  - CSS prefix
  - tier IDs/names
  - view-only vs transactional mode
  - balance overrides
- `ShoppingPage` in `pages/templates/shopping.py` owns:
  - ID namespacing using `suffix`
  - layout construction
  - data access helpers
  - Dash callbacks
  - cart/redeem flow
- Concrete page modules should register Dash page/auth at module top-level, then instantiate `ShoppingPage`.

## Dyson page context

- `pages/dyson-luxe.py` configures `suffix="dyson"`, `assets_folder="dyson"`, `css_prefix="dyson"`, and `db_filename="dyson.db"`.
- It points to network paths for SQLite inventory/shop data and tier CSV.
- `balance_overrides={"OM000000001": 50000}` is a QA/dev shortcut.

## Important recent changes

### Code quality in `pages/templates/shopping.py`

- Added safer OM normalization in `format_om()`.
- Added `is_valid_om()` and validation before patron lookup.
- Normalized OM values before tier, balance, and initials lookup.
- Added tier CSV error handling so missing/locked CSV falls back to SQL.
- Replaced remaining `callback_context.triggered` usage with `ctx.triggered_id`.
- Removed unused `callback_context` import.
- Some inline layout styles were replaced with CSS class names.

### UI/layout in `pages/templates/shopping.py`

- Product cards now use `column is-half-tablet is-one-third-desktop shop-item-column`.
- Main logo uses `shop-logo-wrap` and `shop-main-logo`.
- Refresh button wrapper uses `shop-refresh-wrap`.
- Search area uses `shop-search-container` and `shop-search-panel`.

### Shared styling in `assets/shop.css`

- Added tablet/mobile-friendly sizing for logo, search panel, product cards, modal, footer, and touch targets.
- Made refresh button fixed at the top-right.
- Made `shop-title` no-wrap.
- Centered credit display boxes under their titles.
- Made disabled/locked `search-input` text bright and readable.
- Made placeholders lighter and more readable.
- Removed decorative pseudo-element line/glow from `shop-credits-container`.
- Hid scrollbars while preserving scroll behavior for app/container/modal areas.
- Standardized modal product image height by sizing `shop-modal-image-wrapper` and using `object-fit: contain` on `shop-modal-image`.
- Removed number input spinner buttons for OM number textbox.
- Improved Confirm Your Basket modal styling:
  - basket rows are card-like list items
  - total row is highlighted
  - warning message is pill-style
  - confirm/cancel buttons are rounded and tablet-friendly

### Dyson theme in `assets/dyson/style.css`

- Changed import from `/assets/shop/shop.css` to `/assets/shop.css` because the workspace has `assets/shop.css`.
- Added Dyson-specific logo drop shadow and responsive card title size.

## Validation caveat

- Tried `python -m py_compile pages\templates\shopping.py pages\dyson-luxe.py` but `python` was not found on PATH.
- Tried `py -m py_compile pages\templates\shopping.py pages\dyson-luxe.py` but `py` was also not found on PATH.
- Syntax validation could not be completed via terminal in this environment. Use the project runtime/interpreter if available.

## Things to watch next time

- CSS import path: other themes like `assets/afhc/style.css` may still import `/assets/shop/shop.css`; verify whether that path is intentionally routed or should also become `/assets/shop.css`.
- SQL still uses interpolated UID strings in the template. OM normalization helps, but parameterized SQL would be safer if the `okada` SQL loader supports parameters.
- `read_prize_pool()` is called repeatedly across callbacks. A future performance improvement would be to cache per-check/session or use a store.
- Hidden out-of-stock or unaffordable cards could be changed to disabled cards with labels for better UX.
- If scrollbar hiding still appears, inspect whether Dash/Bulma wraps the page in another scrollable root outside `.shop-main-container`.

## Preferred future workflow

1. Read this file first.
2. Inspect only the specific changed area if needed.
3. Avoid rereading the full `shopping.py` unless changing callback behavior.
4. For visual-only requests, start in `assets/shop.css` and `assets/dyson/style.css`.
5. For campaign/config requests, start in `pages/dyson-luxe.py`.
6. For cart/redeem/data behavior, start in `pages/templates/shopping.py`.

## Expanded agent documentation

Additional persistent reference files now exist under `agent/`:

- `agent/architecture.md` — app architecture, page routing, auth, deployment shape.
- `agent/apis.md` — Flask routes, Dash page interfaces, internal class APIs, external integrations.
- `agent/business_rules.md` — shopping, inventory, redemption, reporting, and UX rules.
- `agent/schema.md` — SQLite schemas, CSV schemas, external table references, Dash store conventions.
- `agent/sql.md` — SQL/query patterns, source systems, data access risks and performance notes.
- `agent/testing.md` — smoke tests, unit test candidates, manual tablet/mobile QA checklist.
- `agent/operations.md` — runtime, network paths, SSL, logging, operational failures.
- `agent/code_map.md` — repository map and what to read first by task type.
