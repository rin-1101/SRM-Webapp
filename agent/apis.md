# APIs, Integrations, and Interfaces

## HTTP / Flask routes

### `GET /check-auth`

Defined in `app.py` and variants.

Returns JSON:

```json
{
  "authenticated": true,
  "port": "8050"
}
```

Purpose:

- Lightweight endpoint for checking Flask-Login authentication state.
- Also returns the server port from request environ.

### `POST /login`

Defined in `app.py` and variants.

Inputs:

- `username` form field
- `password` form field

Process:

1. Lowercase username.
2. Bind to LDAP using `username@int.okadamanila.com`.
3. On bind success, call `login_user(User(username))`.
4. Redirect to session URL or `/home`.
5. On invalid credentials, return simple HTML error with login link.

## Dash page API pattern

Most pages use:

```python
dash.register_page(__name__, path=SOME_ROUTE)
require_login(__name__, access_level=restricted_page[SOME_ROUTE]["access_level"])
```

Layouts are either:

- module-level `layout = ...`
- function `layout()`
- property from a template instance, e.g. `layout = page.layout`

Callbacks use Dash `@callback` or `@app.callback`.

## Internal auth API

File: `utils/login_handler.py`

### `get_accessible_pages_by_role(role)`

Returns a dict mapping page display name to route path for pages whose `access_level` contains the role.

### `require_login(page, **kwargs)`

Marks a Dash page registry entry as restricted and sets access levels.

### `has_access(user, path)`

Checks whether `ACCOUNTS[user.id]["role"]` is allowed for `path`.

## Shopping template API

File: `pages/templates/shopping.py`

### `ShopConfig`

Configuration object for one shop/campaign.

Important parameters:

- `suffix`
- `page_path`
- `access_level`
- `path_db`
- `path_data`
- `path_inv`
- `path_tier_csv`
- `db_filename`
- `orders_table`
- `prize_table`
- `assets_folder`
- `css_prefix`
- `max_per_category`
- `campaign_start`
- `campaign_end`
- `redeemed_window_start`
- `redeemed_window_end`
- `valid_tier_ids`
- `tier_names`
- `currency_label`
- `view_only`
- `balance_overrides`

### `ShoppingPage(module_name, config)`

Builds a namespaced shop page.

Important methods:

- `register_callbacks()`
- `layout` property
- `id(name)` for string IDs
- `wid(component_type, index)` for pattern-matching IDs
- `format_om(om)`
- `is_valid_om(om)`
- `read_prize_pool()`
- `get_tier(uid)`
- `get_balance(uid)`
- `get_redeemed(uid)`
- `get_redeemed_per_category(uid, df)`
- `find_initials(om_number)`
- `allocate_payment(order_items, credits_balance, cp_balance=0)`
- `calculate_total_value(quantities, df)`

## Shop transaction API

File: `utils/app_classes/shop.py`

Class: `ShopTransaction(db_path, db_name, table_name, user)`

Purpose:

- Manage SQLite-backed campaign orders.
- Create tables on init.
- Write separate logs DB under `<db_path>/logs/<db-name>-logs.db`.

Important methods:

- `add_transaction(...)`
- `update_transaction(...)`
- `update_status(trans_id, status)`
- `delete_transaction(trans_id)`
- `show_transactions()`
- `search_transactions(...)`
- `is_redeemed(uid)`
- `get_total_redeemed(uid)`
- `get_all_redemptions(uid)`
- `get_redeemed_by_category(uid, name_to_category, since=None, until=None)`
- `fetch_logs()`
- `get_halo(uid, start_date, end_date, halo_tagging)`

## Inventory API

File: `utils/app_classes/inventory.py`

Class: `Inventory(inv_path, db_name, table_name, user)`

Purpose:

- Manage SQLite-backed prize pool/inventory.
- Create inventory and logs tables on init.
- Use WAL journal mode for safer concurrent reads/writes.

Important methods:

- `add_item(item_id, name, cost, category, inventory)`
- `update_item(item_id, name=None, cost=None, category=None, inventory=None)`
- `delete_item(item_id)`
- `adjust_quantity(item_id, delta)`
- `subtract_quantity(item_id, quantity)`
- `add_quantity(item_id, quantity)`
- `import_csv_to_db(csv_file_path)`
- `get_item_by_id(item_id)`
- `get_item_by_name(name)`
- `show_inventory()`
- `search_items(...)`
- `fetch_logs(...)`
- `prune_logs(days_old=30)`
- `create_new_db(inv_path, db_name, table_name)`

## External SQL loader interface

The app relies heavily on the internal `okada` package:

```python
from okada import SQL
loader = SQL("datamart").get_loader()
df = loader.load_data(sql)
```

Observed connection names:

- `ENGAGE`
- `engage`
- `halo`
- `datamart`
- `hive`

Expected result type: Pandas `DataFrame`.

## External systems

- LDAP: `int.okadamanila.com`.
- ENGAGE SQL Server schemas/tables including `ENGAGEDB.dbo.UC_PL_Player`, `UC_PL_Tier`, `UC_PL_Rating`, `UC_PL_TierPointDetailActual`, and AWA prize redemption tables.
- Datamart/Hive tables such as `dws.dws_mkt_loyaltydb`, `dwd.dwd_mkt_promoredemption`, `dws.dws_mkt_memberprofile`, and `dws.dws_mkt_reinvestment`.
- UNC network paths for SQLite DBs, CSV files, assets, certificates, and shared modules.
