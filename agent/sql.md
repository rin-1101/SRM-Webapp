# SQL and Data Access Notes

## Data access pattern

External data access is mostly through the internal `okada.SQL` loader:

```python
from okada import SQL
loader = SQL("datamart").get_loader()
df = loader.load_data(sql)
```

SQLite data access is through Python `sqlite3` and Pandas `read_sql_query`.

## Observed loader names

- `SQL("ENGAGE")`
- `SQL("engage")`
- `SQL("halo")`
- `SQL("datamart")`
- `SQL("hive")`

Case appears inconsistent. Verify whether the internal `okada` package treats names case-insensitively.

## Shopping SQL

### Read prize pool

```sql
SELECT * FROM prize_pool ORDER BY cost ASC
```

Source: SQLite campaign inventory DB.

### Tier lookup

Fallback query after CSV:

```sql
SELECT UniversalPlayerID,
    CASE
        WHEN TierID = 7 THEN 'Supreme'
        WHEN TierID = 15 THEN 'Maharlika'
        WHEN TierID = 10022 THEN 'Maharlika'
        ELSE 'NA'
    END AS TierName
FROM ENGAGEDB.dbo.UC_PL_Player p
LEFT JOIN ENGAGEDB.dbo.UC_PL_Tier t ON t.PlayerID = p.PlayerID
WHERE UniversalPlayerID = '<uid>'
  AND t.TierID IN (7, 15, 10022)
```

### Tier Point balance

```sql
SELECT p.UniversalPlayerID AS uid, tp.PlayerID, SUM(tp.TierPoint) AS Sum_TP
FROM [ENGAGEDB].[dbo].[UC_PL_Rating] r
LEFT JOIN [ENGAGEDB].[dbo].[UC_PL_Player] p ON r.PlayerID = p.PlayerID
LEFT JOIN [ENGAGEDB].[dbo].[UC_PL_TierPointDetailActual] tp ON r.RatingID = tp.RatingID
WHERE r.TransactionDateTime >= '<campaign_start>'
  AND r.TransactionDateTime  < '<campaign_end>'
  AND p.UniversalPlayerID = '<uid>'
GROUP BY p.UniversalPlayerID, tp.PlayerID
ORDER BY p.UniversalPlayerID, tp.PlayerID
```

### Initials lookup

```sql
SELECT [FirstName] AS fn, [LastName] AS ln
FROM [ENGAGEDB].[dbo].[UC_PL_Player]
WHERE UniversalPlayerID = '<om_number>'
```

## Shop transaction SQL

### Duplicate guard

```sql
SELECT 1 FROM orders
WHERE uid = ?
  AND item_id = ?
  AND item = ?
  AND quantity = ?
  AND cost = ?
  AND ABS(strftime('%s', createddate) - strftime('%s', ?)) <= 30
LIMIT 1
```

### Insert transaction

```sql
INSERT INTO orders
    (uid, createddate, updateddate, item_id, item,
     quantity, cost, total_cost, credits_used, cp_used, status)
VALUES (?,?,?,?,?,?,?,?,?,?,?)
```

### Total redeemed

```sql
SELECT COALESCE(SUM(total_cost), 0) FROM orders WHERE uid=?
```

### Redeemed by category

```sql
SELECT item, SUM(quantity)
FROM orders
WHERE uid=?
  AND createddate >= ?
  AND createddate < ?
GROUP BY item
```

Category is mapped in Python from item name to prize pool category.

## Inventory SQL

### Fetch item

```sql
SELECT ID, name, cost, category, inventory
FROM prize_pool
WHERE ID=?
```

or by name:

```sql
SELECT ID, name, cost, category, inventory
FROM prize_pool
WHERE name=?
```

### Add item

```sql
INSERT INTO prize_pool (ID, name, cost, category, inventory)
VALUES (?,?,?,?,?)
```

### Update item

```sql
UPDATE prize_pool
SET name=?, cost=?, category=?, inventory=?
WHERE ID=?
```

### Atomic quantity adjustment

```sql
UPDATE prize_pool
SET inventory = inventory + ?
WHERE ID = ?
  AND inventory + ? >= 0
```

This prevents negative stock and reduces race conditions.

## Reporting SQL references

### Redemption reports

Files:

- `pages/redemption.py`
- `pages/redemption_daily.py`

Main source:

- `dwd.dwd_mkt_promoredemption`

Common fields:

- `universalplayerid`
- `eventname`
- `prizename`
- `prizedesc`
- `prizevalue`
- `redemptionamount`
- `bucketrequired`
- `redemptiondate`
- `redemptiongamedate`
- `redeemedby`
- `returned`
- `returneddate`
- `returnedby`
- `voucherno`
- `config_sys`

### Casino slip

File: `pages/casinoslip.py`

Uses ENGAGE and likely comp/voucher tables. It also references host/member profile enrichment from datamart.

### Loyalty DB

Files:

- `pages/loyalty_etl/etl.py`
- `pages/loyaltydb_etl/loyalty/data.py`
- `pages/loyaltydb_etl/loyalty/etl.py`

Main sources:

- `dws.dws_mkt_loyaltydb`
- member profile and KPI sources in Hive/datamart.

### Patron ETL

File: `pages/patron_etl/patron_etl.py`

Uses:

- `SQL("datamart")`
- `SQL("engage")`

Queries patron profile, ADT, gaming history, casino win, theoretical win.

## SQL risk notes

- Several external SQL statements are built with f-strings and string interpolation.
- OM input is now normalized in the shopping template, but other pages may still accept raw user input.
- Table names in SQLite queries are interpolated. These are usually config constants, but should still be treated carefully.
- If the `okada` loader supports parameterized queries, future refactors should prefer that.

## Performance notes

- `read_prize_pool()` is called in many shopping callbacks. Caching this per-check/session could reduce repeated SQLite reads.
- External SQL calls inside callbacks can block the UI. Long report queries should consider loading spinners, preview limits, or background jobs.
