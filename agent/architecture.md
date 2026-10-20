# Architecture Notes

## Application shape

This repository is a multi-page Dash application served through Flask. The primary entrypoint is `app.py`, with sibling variants `app_boh.py`, `app_dev.py`, and `app_prod.py` that appear to serve environment/deployment-specific variants.

Core stack:

- Flask server for authentication routes and HTTP headers.
- Dash with `use_pages=True` for page routing.
- Flask-Login for session/user state.
- LDAP via `ldap3` for user authentication.
- Internal `okada` package for SQL loaders and logging.
- SQLite for local campaign inventory/order state.
- Pandas for query results and table transforms.
- Bulma CSS plus custom assets for UI.

## High-level flow

1. `app.py` creates a Flask `server`.
2. Flask routes handle `/login` and `/check-auth`.
3. `Dash(__name__, server=server, use_pages=True, suppress_callback_exceptions=True)` mounts the Dash app.
4. Dash auto-discovers modules under `pages/` that call `dash.register_page()`.
5. Protected pages call `require_login()` from `utils/login_handler.py` after registration.
6. `app.layout` renders `nav_bar`, `dash.page_container`, and `footer`.
7. Page modules define layouts and callbacks.

## Authentication and authorization

### Login

- Flask POST route `/login` accepts username/password from form data.
- Username is lowercased.
- LDAP server is configured through `LDAP_SERVER`, currently set in process env to `int.okadamanila.com`.
- LDAP bind uses `username + "@" + LDAP_SERVER`.
- On success, a lightweight `User` object is logged in with Flask-Login.
- Redirect target comes from `session["url"]` if present, otherwise `/home`.

### Session/security headers

- Secret key is generated at runtime using `secrets.token_hex(32)`.
- Cookie name: `sessionSM`.
- Cookies are HTTP-only, secure, and SameSite Lax.
- `X-Frame-Options: DENY` is added after each request.
- Requests to host starting with `10.36.21.60` redirect to `https://srm.okadamanila.com:8050`.

### Authorization

- `utils/login_handler.py` loads accounts from `get_users()` and stores them in `ACCOUNTS`.
- Page access rules are declared in `restricted_page` keyed by route path.
- Human labels are declared in `pages_name`.
- `require_login(page, access_level=...)` marks the registered Dash page as restricted.
- `has_access(user, path)` checks `ACCOUNTS[user.id]["role"]` against `restricted_page[path]["access_level"]`.

## Routing and page registry

Route constants live in `utils/paths.py`. Important routes include:

- `/redemption`
- `/redemptiondaily`
- `/casinoslip`
- `/loyalty`
- `/comms`
- `/fire-horse`
- `/fire-horse-view`
- `/transactions`
- `/transactions-view`
- `/inventory`
- `/patron`
- `/rfr-raffle`
- `/rfr-raffle-grand`
- `/rfr-checker`
- `/dyson-luxe-rewards`

## Main feature groups

### Shopping / redemption campaigns

Main files:

- `pages/templates/shopping.py`
- `pages/dyson-luxe.py`
- `pages/fire_horse.py`
- `pages/fire_horse_view.py`
- `utils/app_classes/shop.py`
- `utils/app_classes/inventory.py`
- `assets/shop.css`
- `assets/dyson/style.css`

`pages/templates/shopping.py` contains a reusable `ShopConfig` + `ShoppingPage` template that builds the browse → add to cart → redeem workflow. Concrete campaign pages instantiate it with campaign-specific paths, dates, assets, and DB names.

### Inventory management

Main files:

- `pages/inventory-management.py`
- `utils/app_classes/inventory.py`

This page lists SQLite inventory DB files, creates new DBs, uploads CSV inventory, searches items, and adds/updates/deletes items.

### Transactions reporting

Main files:

- `pages/transactions.py`
- `pages/transactions-view.py`
- `utils/app_classes/shop.py`

These pages query external HALO/ENGAGE data and/or local SQLite shop order data for redemption transaction visibility.

### Raffle pages

Main files:

- `pages/templates/raffle.py`
- `pages/rfr_raffle.py`
- `pages/rfr_raffle_grand.py`
- `pages/wed_raffle.py`
- `pages/raffle-control.py`
- `pages/raffle_etl/`

Raffle implementations use template/config patterns similar to the shopping template.

### Reports / dashboards

Main files:

- `pages/redemption.py`
- `pages/redemption_daily.py`
- `pages/casinoslip.py`
- `pages/loyaltydb_report.py`
- `pages/patron.py`
- `pages/comms.py`

These pages query datamart/ENGAGE/Hive sources through the internal `okada.SQL` loader and render Dash tables/charts/downloads.

## Asset architecture

- Shared styles: `assets/bulma.css`, `assets/shop.css`, `assets/raffle.css`.
- Per-campaign theme folders: `assets/dyson/`, `assets/afhc/`, `assets/DEFAULT/`.
- Inventory item images are under `assets/inventory/<campaign>/<ID>.png`.
- For the Dyson campaign, images are `assets/inventory/dyson/1.png` to `4.png`.

## Deployment notes

- `app.py` runs SSL on host `0.0.0.0`, port `8050`.
- Cert path points to `\\OMPYTSRVD00001V\testssl`.
- Several modules append network paths to `sys.path` to import `okada` and app classes.
- Many paths are UNC network paths under `\\ominfstdpsd10001p-fs.int.okadamanila.com\Casino\Strategic Marketing\...`.

## Known architecture risks

- Runtime-generated secret key means sessions may invalidate on restart.
- Some SQL queries interpolate user-controlled or campaign-controlled strings directly.
- Several page files duplicate patterns and may register the same page twice.
- Project vendors packages like `dash_auth`, `flask_login`, `flask_sqlalchemy`, `ldap3`, etc. inside the repo, which can make dependency/version tracking ambiguous.
- Python CLI was not available in the terminal during validation; use the real app interpreter for tests.
