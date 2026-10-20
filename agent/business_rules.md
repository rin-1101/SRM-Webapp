# Business Rules

## Authentication and access control

- Users authenticate through LDAP.
- User roles are loaded from CSV/user utilities via `utils.get_users.get_users()`.
- Page access is role-based through `restricted_page` in `utils/login_handler.py`.
- Unauthorized pages should be protected by calling `require_login()` after `dash.register_page()`.

## Shopping campaign qualification

Implemented mainly in `pages/templates/shopping.py`.

### OM number handling

- OM inputs are normalized to `OM` + 9-digit number.
- Empty/non-numeric inputs are rejected before lookup.
- Example: `1` becomes `OM000000001`.

### Tier qualification

- Tier is checked first against a cached CSV snapshot (`path_tier_csv`).
- If CSV is unavailable or missing, logic falls back to SQL lookup.
- Default valid tier IDs are `(7, 15, 10022)`.
- Default tier names:
  - `7` → `Supreme`
  - `15` → `Maharlika`
  - `10022` → `Maharlika`
- If tier resolves to `NA`, patron is not qualified.

### Earning / balance rules

- Balance is based on summed Tier Points during `campaign_start <= TransactionDateTime < campaign_end`.
- Balance uses `math.ceil()` of positive TP sum.
- `balance_overrides` can force balance for QA/dev OM numbers.
- If balance is less than `1`, patron is rejected with no earning.

### Redeemed balance rules

- Total available balance = earned balance - total redeemed.
- `ShopTransaction.get_total_redeemed(uid)` sums all `total_cost` rows for a player.
- Available balance cannot go below `0`.

### Item visibility

- Item cards are built from SQLite `prize_pool` ordered by cost.
- Items are hidden if:
  - `inventory == 0`
  - `cost > available balance`

### Quantity rules

- User opens item modal by tapping a card.
- Quantity defaults to cart quantity already selected for that item.
- `+` is allowed only if all are true:
  - proposed quantity is not above current inventory
  - total cart cost remains within available balance
  - redeemed + current cart quantity in same category does not exceed `max_per_category`
- `-` cannot reduce below `0`.

### Category limits

- Default `max_per_category` is `3`.
- Previous category redemptions are calculated within `redeemed_window_start <= createddate < redeemed_window_end`.
- Warning messages:
  - Already at max: `⚠️ You have already redeemed the max (...) for this category.`
  - Some previous redemption: `ℹ️ You have redeemed X of Y allowed for this category.`

### Cart rules

- Add to cart stores quantities in a Dash `dcc.Store` keyed by dataframe index string.
- Quantity `0` removes the item from cart.
- Total value is recalculated from prize pool cost × quantity.

### Redemption confirmation rules

- Pressing `REDEEM` opens Confirm Your Basket modal.
- Basket rows show item, quantity, and total points.
- If no items selected, modal says `No items selected.`
- Confirm button has a duplicate-click guard: ignores confirms within 1500 ms.

### Redemption transaction rules

On confirm:

1. Re-read prize pool.
2. Create `ShopTransaction` and `Inventory` instances.
3. For each cart item:
   - Skip zero quantity.
   - Look up current stock by item name.
   - If missing or insufficient, fail redemption and show stock errors.
   - Build `order_items` with item name, quantity, unit points, total, item ID.
4. Recalculate redeemed total.
5. Effective credits = current earned credits - redeemed total.
6. Allocate credits through `allocate_payment()`.
7. Add order rows with status `pending`.
8. For successful rows, subtract inventory atomically.
9. On success, show success message and clear OM textbox.

## Inventory management rules

Implemented in `utils/app_classes/inventory.py` and `pages/inventory-management.py`.

- Inventory item fields:
  - `ID`
  - `name`
  - `cost`
  - `category`
  - `inventory`
- Validation:
  - `item_id` must be integer.
  - `name` must be non-empty string.
  - `category` must be non-empty string.
  - `cost` must be non-negative integer.
  - `inventory` must be non-negative integer.
- SQLite table has `CHECK(inventory >= 0)`.
- `adjust_quantity()` updates inventory atomically with guard `inventory + delta >= 0`.
- CSV import requires lowercase columns: `id`, `name`, `cost`, `category`, `inventory`.

## Transaction duplicate rules

Implemented in `utils/app_classes/shop.py`.

- `add_transaction()` rejects duplicate rows if same `uid`, `item_id`, `item`, `quantity`, and `cost` occurred within 30 seconds.
- Return values:
  - `True` for inserted
  - `False` for skipped duplicate
  - string error for failure

## Reporting rules

### Redemption reports

- `pages/redemption.py` and `pages/redemption_daily.py` query promotional redemption tables.
- Preview mode limits rows.
- Download callbacks export report data.

### Casino slip report

- `pages/casinoslip.py` queries ENGAGE voucher/comp data.
- Adds host/nationality enrichment from datamart where enabled/commented.

### Loyalty database

- ETL/query modules read `dws.dws_mkt_loyaltydb`, profile, KPI, and rated play data.
- Loyalty group sorting appears to use: `Prime`, `Elite`, `Premium`, `Supreme`, `Maharlika`, `Okada VIP`.

## UX rules recently established

- App is primarily tablet/mobile web-app usage.
- Touch targets should be large.
- Scrollbars should be hidden while retaining scrolling.
- Modal product images should use consistent fixed responsive wrapper heights.
- Locked/disabled textboxes and placeholders should be light/readable.
- `shop-title` should not wrap.
- Refresh button should remain fixed.
