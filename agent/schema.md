# Schema and Data Model Notes

## SQLite databases

The shopping/inventory system uses local SQLite files under network folders, generally:

- Inventory DB folder: `...\reports\sqlite\inventory`
- Shop/orders DB folder: `...\reports\sqlite\shop`
- Logs folder under each DB folder: `logs/`

Campaign DB examples:

- `dyson.db`
- `afhc.db`

## Inventory table: `prize_pool`

Created by `Inventory._init_inventory_table()`.

```sql
CREATE TABLE IF NOT EXISTS prize_pool (
    ID        INTEGER PRIMARY KEY AUTOINCREMENT,
    name      TEXT    NOT NULL,
    cost      INTEGER NOT NULL,
    category  TEXT    NOT NULL,
    inventory INTEGER NOT NULL CHECK(inventory >= 0)
)
```

Notes:

- Table name is configurable through `ShopConfig.prize_table`, default `prize_pool`.
- `ID` maps to inventory image filename: `/assets/inventory/<assets_folder>/<ID>.png`.
- `cost` is points cost, displayed with `currency_label`, default `TP`.
- `category` drives per-category redemption limits.
- `inventory` controls stock visibility and redemption guard.

## Orders table: `orders`

Created by `ShopTransaction._init_orders_table()`.

```sql
CREATE TABLE IF NOT EXISTS orders (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    uid          TEXT    NOT NULL,
    createddate  TEXT    NOT NULL,
    updateddate  TEXT    NOT NULL,
    item_id      INTEGER NOT NULL,
    item         TEXT    NOT NULL,
    quantity     INTEGER NOT NULL,
    cost         INTEGER NOT NULL,
    total_cost   INTEGER NOT NULL,
    credits_used INTEGER NOT NULL DEFAULT 0,
    cp_used      INTEGER NOT NULL DEFAULT 0,
    status       TEXT    NOT NULL DEFAULT 'pending'
)
```

Notes:

- Table name is configurable through `ShopConfig.orders_table`, default `orders`.
- `uid` is OM-formatted universal player ID.
- `total_cost` is `quantity * cost` per row.
- Old `total_value` column is intentionally not used.
- `status` defaults to `pending`.
- `credits_used` and `cp_used` support split payment logic.

## Logs table

Both `Inventory` and `ShopTransaction` create logs tables in a separate logs DB.

```sql
CREATE TABLE IF NOT EXISTS logs (
    ID        INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    user      TEXT NOT NULL,
    action    TEXT NOT NULL,
    status    TEXT NOT NULL,
    details   TEXT
)
```

Log DB naming:

- `<db_folder>/logs/<db-stem>-logs.db`

Examples:

- `sqlite/shop/logs/dyson-logs.db`
- `sqlite/inventory/logs/dyson-logs.db`

## Tier snapshot CSV

Used by `ShoppingPage.get_tier()`.

Expected columns:

- `UniversalPlayerID`
- `Tier`

Behavior:

- `UniversalPlayerID` is converted to string and stripped.
- If UID is found, return CSV `Tier`.
- If CSV read fails or UID missing, fall back to SQL.

## Inventory CSV import schema

Used by `Inventory.import_csv_to_db()` and inventory management upload logic.

Required columns:

- `id`
- `name`
- `cost`
- `category`
- `inventory`

Validation converts numeric fields to integers and rejects missing/invalid rows.

## External SQL table references

### ENGAGE / HALO player and tier tables

Observed in shopping and patron code:

- `ENGAGEDB.dbo.UC_PL_Player`
  - `UniversalPlayerID`
  - `PlayerID`
  - `FirstName`
  - `LastName`
- `ENGAGEDB.dbo.UC_PL_Tier`
  - `PlayerID`
  - `TierID`
- `ENGAGEDB.dbo.UC_PL_Rating`
  - `RatingID`
  - `PlayerID`
  - `TransactionDateTime`
- `ENGAGEDB.dbo.UC_PL_TierPointDetailActual`
  - `RatingID`
  - `PlayerID`
  - `TierPoint`

### ENGAGE AWA prize redemption tables

Observed in `ShopTransaction.get_halo()` and transactions pages:

- `ENGAGEDB.AWA.UC_PL_PrizeRedemption`
- `ENGAGEDB.AWA.UC_X_EventDefinition`
- `ENGAGEDB.AWA.UC_PL_PrizeRedemptionDetail`
- `ENGAGEDB.dbo.UC_PL_Player`

Common derived fields:

- GameDate: if redemption hour is before 6 AM, subtract one day.
- Returned rows are excluded by checking `Returned IS NULL`.

### Datamart / Hive reporting tables

Observed references:

- `dwd.dwd_mkt_promoredemption`
- `dws.dws_mkt_memberprofile`
- `dws.dws_mkt_loyaltydb`
- `dws.dws_mkt_reinvestment`

## Dash stores in shopping page

Important `dcc.Store` IDs are suffixed per campaign:

- `visible-rows-<suffix>`
- `item-limit-store-<suffix>`
- `modal-item-index-<suffix>`
- `current-quantity-<suffix>`
- `token-<suffix>`
- `red-<suffix>`
- `selected-item-id-<suffix>`
- `df-length-<suffix>`
- `details-visibility-<suffix>`
- `prev-redeemed-by-cat-<suffix>`
- `quantities-store-<suffix>`
- `cart-value-<suffix>`
- `last-confirm-ts-<suffix>`

## ID naming convention

Shopping pages namespace all component IDs by suffix:

- String ID: `<name>-<suffix>`
- Pattern ID: `{ "type": "<component_type>-<suffix>", "index": <index> }`

This allows multiple shopping pages to coexist without ID collisions.
