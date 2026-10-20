# Code Map

## Root files

- `app.py` — main Flask/Dash app entrypoint.
- `app_boh.py`, `app_dev.py`, `app_prod.py` — app variants.
- `.gitignore` — git ignore rules.

## `agent/`

Persistent AI-maintained repository notes.

- `agent/brain.md` — high-level memory and recent-change summary.
- `agent/architecture.md` — architecture overview.
- `agent/apis.md` — interfaces/APIs/integrations.
- `agent/business_rules.md` — business rules.
- `agent/schema.md` — schemas/data model.
- `agent/sql.md` — SQL/data access notes.
- `agent/testing.md` — test strategy and checklists.
- `agent/operations.md` — deployment/ops notes.
- `agent/code_map.md` — this file.

## `assets/`

Static files auto-served by Dash.

- `assets/bulma.css` — Bulma CSS.
- `assets/shop.css` — shared shop UI stylesheet.
- `assets/shop-old.css` — old shop CSS backup.
- `assets/raffle.css` — raffle styles.
- `assets/dyson/` — Dyson campaign theme assets.
- `assets/afhc/` — AFHC campaign theme assets.
- `assets/DEFAULT/` — default images and UI assets.
- `assets/inventory/dyson/` — product images for Dyson inventory IDs.

## `utils/`

Shared app utilities.

- `utils/paths.py` — route constants.
- `utils/login_handler.py` — access control map and auth helpers.
- `utils/get_users.py` — loads account/role data.
- `utils/page_loader.py` — dynamic page loading helper.
- `utils/users.csv`, `utils/bd_users.csv`, `utils/bd2_users.csv` — user/role source data.

## `utils/app_classes/`

Reusable business/data classes.

- `inventory.py` — SQLite inventory/prize pool manager.
- `shop.py` — SQLite shop transaction/order manager.
- `patron.py` — patron data helper using ENGAGE/datamart.
- `dashboard_helper.py` — dashboard helper functions.
- `colorgame.py`, `guesshistory.py` — game-related helper classes.

## `pages/`

Dash pages.

### Core pages

- `pages/home.py` — home page.
- `pages/login.py` — login page layout.
- `pages/logout.py` — logout page.
- `pages/about.py` — about page.
- `pages/permission.py` — permission page.

### Reports

- `pages/redemption.py` — redemption report.
- `pages/redemption_daily.py` — daily redemption report.
- `pages/casinoslip.py` — casino slip report.
- `pages/loyaltydb_report.py` — loyalty database dashboard/report.
- `pages/patron.py` — patron detail/dashboard page.
- `pages/tierreport.py` — tier report page.

### Shopping/campaign pages

- `pages/dyson-luxe.py` — Dyson Luxe Rewards campaign page.
- `pages/fire_horse.py` — Fire Horse shopping campaign page.
- `pages/fire_horse_view.py` — older/standalone Fire Horse view page.
- `pages/inventory-management.py` — inventory DB manager.
- `pages/transactions.py` — shop transaction/admin page.
- `pages/transactions-view.py` — transaction viewing page.

### Raffles

- `pages/rfr_raffle.py` — Reels for Relaxation raffle.
- `pages/rfr_raffle_grand.py` — Reels for Relaxation grand draw.
- `pages/rfr-checker.py` — RFR checker.
- `pages/wed_raffle.py` / `pages/wed_raffle-grand.py` — Win It Wednesday raffle pages.
- `pages/raffle-control.py` — raffle backend/control page.
- `pages/raffle.py` — simple/sample raffle page.

### Communications

- `pages/comms.py` — SMS/comms UI.
- `pages/sms_etl/sms.py` — SMS ETL/helper logic.

## `pages/templates/`

Reusable page templates.

- `pages/templates/shopping.py` — generic shop/cart/redeem template.
- `pages/templates/raffle.py` — generic raffle template.
- `pages/templates/raffle-wed.py` — older/commented Wed raffle template.

## ETL packages under `pages/`

- `pages/loyalty_etl/`
- `pages/loyaltydb_etl/`
- `pages/overcomp_etl/`
- `pages/patron_etl/`
- `pages/raffle_etl/`
- `pages/sms_etl/`

These are data-loading/transformation helpers used by pages/reports.

## Vendored/external package folders

The repo contains local copies of packages:

- `cachelib/`
- `dash_auth/`
- `dash_auth-2.0.0/`
- `flask_login/`
- `flask_session/`
- `flask_sqlalchemy/`
- `ldap3/`
- `msgspec/`

Be aware these can shadow installed packages.

## Data/document folders

- `documents/` — campaign CSVs/XLSX/HTML and inventory source files.
- `csv/` — CSV data folder.
- `sqlite/` — local SQLite data folder.
- `config/` — YAML config, currently includes `comms.yaml`.

## Most important files to read first by task type

### App startup/auth/routing

1. `app.py`
2. `utils/login_handler.py`
3. `utils/paths.py`
4. `pages/home.py`

### Shopping/Dyson UI

1. `agent/brain.md`
2. `pages/dyson-luxe.py`
3. `pages/templates/shopping.py`
4. `assets/shop.css`
5. `assets/dyson/style.css`

### Inventory/orders

1. `utils/app_classes/inventory.py`
2. `utils/app_classes/shop.py`
3. `pages/inventory-management.py`
4. `pages/transactions.py`
5. `pages/transactions-view.py`

### Reports/SQL

1. `agent/sql.md`
2. Target page file under `pages/`
3. Relevant ETL folder under `pages/*_etl/`

### Raffles

1. `pages/templates/raffle.py`
2. `pages/rfr_raffle.py`
3. `pages/rfr_raffle_grand.py`
4. `pages/raffle-control.py`
5. `pages/raffle_etl/`
