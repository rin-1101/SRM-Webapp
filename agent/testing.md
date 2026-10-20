# Testing and Validation Notes

## Current validation limitation

During recent work, terminal validation could not run because Python was unavailable on PATH:

- `python -m py_compile ...` failed with Microsoft Store alias message.
- `py -m py_compile ...` failed because `py` is not recognized.

Use the actual project/runtime Python interpreter if available in VS Code, a virtual environment, or the deployment server.

## Recommended smoke tests

### App startup

1. Start the Dash app using the actual interpreter.
2. Confirm `app.py` starts without import errors.
3. Confirm LDAP/login page loads.
4. Confirm `/check-auth` returns JSON.
5. Confirm main navigation renders.

### Authentication

1. Login with a valid LDAP user.
2. Login with invalid credentials and confirm rejection.
3. Confirm restricted pages redirect unauthenticated users to `/login`.
4. Confirm role-based nav only shows accessible pages.

### Dyson shopping page

Route: `/dyson-luxe-rewards`

1. Open the page on tablet viewport.
2. Confirm logo/theme loads from `assets/dyson/style.css` and `assets/shop.css`.
3. Enter QA OM `1`; confirm it normalizes to `OM000000001` internally and uses balance override.
4. Confirm initials/tier fields are readable when disabled.
5. Confirm placeholders are readable.
6. Confirm OM number input has no spinner controls.
7. Confirm refresh button is fixed.
8. Confirm credit titles do not wrap.
9. Confirm credit boxes are centered below titles.
10. Confirm scrollbars are hidden but the page still scrolls.
11. Tap item cards and confirm modal opens.
12. Confirm modal images maintain consistent height across items.
13. Add quantities and confirm cart total updates.
14. Confirm category max of 3 is enforced.
15. Confirm Confirm Your Basket modal styling is acceptable.
16. Confirm duplicate confirm click is guarded.

### Inventory management

Route: `/inventory`

1. Confirm DB dropdown loads DB files from inventory folder.
2. Create a test DB if safe.
3. Upload a CSV with columns `id,name,cost,category,inventory`.
4. Search by name/category/cost.
5. Add an item.
6. Update an item.
7. Delete an item.
8. Confirm inventory cannot go negative through `adjust_quantity()`.

### Transaction records

1. Perform a redemption in a test DB.
2. Confirm row appears in `orders` table.
3. Confirm `total_cost = quantity * cost`.
4. Confirm inventory decreased.
5. Confirm logs DB has actions.
6. Try rapid double-confirm and confirm only one transaction set is inserted.

### Reports

For each major report page:

- Redemption
- Redemption Daily
- Casino Slip
- Loyalty DB
- Patron
- Transactions
- Transactions View

Smoke test:

1. Page loads.
2. Query callback runs with preview/default values.
3. Empty result is handled gracefully.
4. Download callback works if present.
5. Large query does not freeze the app for too long.

## Unit test candidates

### Pure shopping helpers

These can be tested without Dash server:

- `ShoppingPage.format_om()`
- `ShoppingPage.is_valid_om()`
- `ShoppingPage.get_gamedate()`
- `ShoppingPage.allocate_payment()`
- `ShoppingPage.calculate_total_value()`
- `_category_warning()` with a minimal configured page instance

Example expectations:

- `format_om(1)` → `OM000000001`
- `format_om("OM123")` → `OM000000123`
- `format_om(None)` → empty string
- `is_valid_om(None)` → `False`
- `allocate_payment()` spends credits before CP.

### Inventory class

Use a temporary SQLite DB folder.

Test:

- DB/table creation.
- Add valid item.
- Reject invalid item fields.
- Search items.
- Atomic decrement succeeds when enough stock.
- Atomic decrement fails when stock would go negative.
- Logs are written without crashing callers.

### ShopTransaction class

Use a temporary SQLite DB folder.

Test:

- DB/table creation.
- Add transaction.
- Duplicate transaction within 30 seconds returns `False`.
- Search transactions.
- Update transaction recalculates total cost.
- Delete transaction.
- Total redeemed sums `total_cost`.
- Redeemed by category maps names to categories.

## Manual visual QA checklist for tablet/mobile

- Portrait and landscape tablet view.
- Touch targets at least ~44px high.
- No horizontal scrollbar.
- Fixed footer does not cover content.
- Fixed refresh button does not cover important fields.
- Modal is centered and not taller than viewport.
- Confirm modal footer buttons remain visible.
- Disabled fields and placeholders have enough contrast.
- Product names wrap cleanly in cards.

## Regression hotspots

- CSS changes in `assets/shop.css` can affect all shop-themed campaigns, not only Dyson.
- `assets/afhc/style.css` may still import `/assets/shop/shop.css`; verify before assuming shared CSS applies to AFHC.
- Callback output counts in `ShoppingPage.validate_player()` depend on `view_only` mode; be careful when editing.
- `ShoppingPage._register_callbacks()` returns early for `view_only=True`; cart/redeem callbacks should not be registered in view-only mode.
- SQLite table schemas are created on class init; schema changes require migration handling for existing DB files.
