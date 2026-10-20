# Operations and Deployment Notes

## Entrypoints

- Main: `app.py`
- Variants: `app_boh.py`, `app_dev.py`, `app_prod.py`

All variants appear to follow the same Flask + Dash + LDAP architecture.

## Runtime

`app.py` runs:

```python
app.run_server(
    debug=False,
    host="0.0.0.0",
    port=8050,
    ssl_context=(cert_file, key_file),
)
```

SSL cert path:

- `\\OMPYTSRVD00001V\testssl\wildcard_okadamanila_com.pem`
- `\\OMPYTSRVD00001V\testssl\wildcard_okadamanila_com_key.pem`

## Network dependencies

The app relies on UNC paths, including:

- `\\ominfstdpsd10001p-fs.int.okadamanila.com\Casino\Strategic Marketing\Database Admin\ETL\Applications\okada`
- `\\ominfstdpsd10001p-fs.int.okadamanila.com\Casino\Strategic Marketing\Database Admin\ETL\Applications\reports`
- SQLite DB folders under `reports\sqlite\...`
- Assets under `reports\assets\...`
- Campaign data and tier snapshots under Marketing Analysis campaign folders.

If the app fails at import time, verify network drive/share availability first.

## Environment variables set in app

- `LDAP_SERVER=int.okadamanila.com`
- `SECRET_KEY=<generated session id>`

Note: there is a TODO in `app.py` to move secrets/env config to `.env`.

## Session cookies

- Cookie name: `sessionSM`
- HTTP-only: `True`
- Secure: `True`
- SameSite: `Lax`

## Logging

- `okada.LogService` is used in the shopping template.
- `Inventory` and `ShopTransaction` write SQLite logs tables.
- Inventory logs and shop logs are in separate DBs under a `logs` folder.
- `_log()` methods intentionally swallow errors to prevent logging failures from crashing transactions.

## Local/generated DB files

SQLite files live under `sqlite/` or network SQLite folders.

Important campaign DB example:

- `dyson.db`

Tables created automatically if missing:

- `prize_pool`
- `orders`
- `logs`

## Assets

Dash serves files under `assets/` automatically.

Important paths:

- `assets/shop.css`
- `assets/dyson/style.css`
- `assets/dyson/bg.png`
- `assets/dyson/logo.png`
- `assets/inventory/dyson/<ID>.png`

## Common operational failures

### Python command missing

In this environment, both `python` and `py` commands were unavailable. Use the correct interpreter path from VS Code/deployment environment.

### LDAP bind failure

Check:

- network connectivity to `int.okadamanila.com`
- username format
- password validity
- SSL requirements

### Page import failure

Check:

- UNC paths appended to `sys.path`
- `okada` package availability
- vendored dependencies shadowing installed dependencies
- missing assets/files referenced at import time

### Shopping page failure

Check:

- `path_db` points to existing SQLite DB.
- `prize_pool` table exists or can be created.
- `path_data` and `path_inv` are writable.
- `path_tier_csv` exists or SQL fallback is available.
- Item images exist for every `prize_pool.ID`.

### Inventory upload failure

CSV must have columns:

- `id`
- `name`
- `cost`
- `category`
- `inventory`

## Maintenance recommendations

- Move secrets and paths to config/environment variables.
- Add a known interpreter path or virtual environment instructions.
- Add a small test suite for `Inventory`, `ShopTransaction`, and pure shopping helpers.
- Add migration scripts for SQLite schema changes.
- Normalize `SQL("...")` loader names.
- Review direct SQL interpolation.
- Keep `agent/` docs updated after significant changes.
