"""
inventory.py — Inventory
Manages a SQLite-backed prize pool / inventory table.
"""

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd


# ------------------------------------------------------------------
# Standalone validation (no DB access needed)
# ------------------------------------------------------------------

def _validate_item(item_id: int, name: str, cost: int, category: str, inventory: int) -> Optional[str]:
    """Return an error string on failure, None if valid."""
    if not isinstance(item_id, int):
        return "item_id must be an integer."
    if not isinstance(name, str) or not name.strip():
        return "name must be a non-empty string."
    if not isinstance(category, str) or not category.strip():
        return "category must be a non-empty string."
    if not isinstance(cost, int) or cost < 0:
        return "cost must be a non-negative integer."
    if not isinstance(inventory, int) or inventory < 0:
        return "inventory must be a non-negative integer."
    return None


class Inventory:
    """
    Manages a SQLite-backed inventory table for campaign prizes.

    Parameters
    ----------
    inv_path   : folder that contains the SQLite file
    db_name    : filename, e.g. "afhc.db"
    table_name : inventory table name, e.g. "prize_pool"
    user       : identifier written to every log row
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(self, inv_path: str, db_name: str, table_name: str, user: str):
        self.path  = os.path.join(inv_path, db_name)
        self.table = table_name
        self.user  = user

        log_dir = os.path.join(inv_path, "logs")
        os.makedirs(log_dir, exist_ok=True)
        self.log_path = os.path.join(log_dir, f"{os.path.splitext(db_name)[0]}-logs.db")

        self._init_logs_table()
        self._init_inventory_table()

    # ------------------------------------------------------------------
    # Internal utilities
    # ------------------------------------------------------------------

    @contextmanager
    def _get_conn(self, path: Optional[str] = None):
        """
        Yield a (conn, cursor) pair, always closing both on exit.
        WAL mode makes concurrent reads safe alongside writes.
        """
        conn = sqlite3.connect(path or self.path)
        conn.execute("PRAGMA journal_mode=WAL")
        cur  = conn.cursor()
        try:
            yield conn, cur
        finally:
            cur.close()
            conn.close()

    def _log(self, action: str, status: str, details: Optional[str] = None) -> None:
        """Write a log row. Silently swallows its own errors."""
        try:
            with self._get_conn(self.log_path) as (conn, cur):
                cur.execute(
                    "INSERT INTO logs (timestamp, user, action, status, details) VALUES (?,?,?,?,?)",
                    (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.user, action, status, details),
                )
                conn.commit()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Schema creation
    # ------------------------------------------------------------------

    def _init_logs_table(self) -> None:
        with self._get_conn(self.log_path) as (conn, cur):
            cur.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    ID        INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    user      TEXT NOT NULL,
                    action    TEXT NOT NULL,
                    status    TEXT NOT NULL,
                    details   TEXT
                )
            """)
            conn.commit()

    def _init_inventory_table(self) -> bool:
        try:
            with self._get_conn() as (conn, cur):
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self.table} (
                        ID        INTEGER PRIMARY KEY AUTOINCREMENT,
                        name      TEXT    NOT NULL,
                        cost      INTEGER NOT NULL,
                        category  TEXT    NOT NULL,
                        inventory INTEGER NOT NULL CHECK(inventory >= 0)
                    )
                """)
                conn.commit()
            self._log("INIT_DB", "SUCCESS", f"Table '{self.table}' ready.")
            return True
        except Exception as e:
            self._log("INIT_DB", "ERROR", str(e))
            return False

    # ------------------------------------------------------------------
    # Private fetch helper
    # ------------------------------------------------------------------

    def _fetch_item(self, where_col: str, where_val) -> Optional[dict]:
        """
        Return a single item dict or None.
        Used by get_item_by_id() and get_item_by_name().
        """
        try:
            with self._get_conn() as (conn, cur):
                cur.execute(
                    f"SELECT ID, name, cost, category, inventory FROM {self.table} WHERE {where_col}=?",
                    (where_val,)
                )
                row = cur.fetchone()
            if row:
                return {"id": row[0], "name": row[1], "cost": row[2],
                        "category": row[3], "inventory": row[4]}
            return None
        except Exception as e:
            self._log("FETCH_ITEM", "ERROR", str(e))
            return None

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def add_item(self, item_id: int, name: str, cost: int, category: str, inventory: int):
        err = _validate_item(item_id, name, cost, category, inventory)
        if err:
            return err
        try:
            with self._get_conn() as (conn, cur):
                cur.execute(
                    f"INSERT INTO {self.table} (ID, name, cost, category, inventory) VALUES (?,?,?,?,?)",
                    (item_id, name, cost, category, inventory)
                )
                conn.commit()
            self._log("ADD_ITEM", "SUCCESS",
                      f"ID={item_id}, name={name}, cost={cost}, category={category}, inventory={inventory}")
            return True
        except Exception as e:
            self._log("ADD_ITEM", "ERROR", str(e))
            return str(e)

    def update_item(
        self,
        item_id:   int,
        name:      Optional[str] = None,
        cost:      Optional[int] = None,
        category:  Optional[str] = None,
        inventory: Optional[int] = None,
    ):
        """Partial update — only supplied (non-None, non-empty) fields are changed."""
        item = self._fetch_item("ID", item_id)
        if item is None:
            msg = f"No item found with ID={item_id}"
            self._log("UPDATE_ITEM", "ERROR", msg)
            return msg

        new_name  = name      if name      not in (None, "") else item["name"]
        new_cost  = cost      if cost      not in (None, "") else item["cost"]
        new_cat   = category  if category  not in (None, "") else item["category"]
        new_inv   = inventory if inventory not in (None, "") else item["inventory"]

        err = _validate_item(item_id, new_name, new_cost, new_cat, new_inv)
        if err:
            return err

        try:
            with self._get_conn() as (conn, cur):
                cur.execute(
                    f"UPDATE {self.table} SET name=?, cost=?, category=?, inventory=? WHERE ID=?",
                    (new_name, new_cost, new_cat, new_inv, item_id)
                )
                conn.commit()
            self._log("UPDATE_ITEM", "SUCCESS",
                      f"ID={item_id}: name={new_name}, cost={new_cost}, category={new_cat}, inventory={new_inv}")
            return True
        except Exception as e:
            self._log("UPDATE_ITEM", "ERROR", str(e))
            return str(e)

    def delete_item(self, item_id: int):
        try:
            with self._get_conn() as (conn, cur):
                cur.execute(f"DELETE FROM {self.table} WHERE ID=?", (item_id,))
                deleted = cur.rowcount
                conn.commit()
            if deleted == 0:
                msg = f"No item found with ID={item_id}"
                self._log("DELETE_ITEM", "ERROR", msg)
                return msg
            self._log("DELETE_ITEM", "SUCCESS", f"Deleted ID={item_id}")
            return True
        except Exception as e:
            self._log("DELETE_ITEM", "ERROR", str(e))
            return str(e)

    def adjust_quantity(self, item_id: int, delta: int):
        """
        Atomically add `delta` to inventory.  Use negative delta to subtract.

        This replaces the original separate subtract_quantity / add_quantity
        methods.  The WHERE inventory + ? >= 0 guard makes the check and the
        write happen in a single SQL statement, eliminating the read-then-write
        race condition the original had (read stock → compute new → write).

        Returns True, an error string, or raises nothing.
        """
        if delta == 0:
            return True
        try:
            with self._get_conn() as (conn, cur):
                cur.execute(
                    f"""UPDATE {self.table}
                           SET inventory = inventory + ?
                         WHERE ID = ?
                           AND inventory + ? >= 0""",
                    (delta, item_id, delta)
                )
                updated = cur.rowcount
                conn.commit()

            if updated == 0:
                # Either item not found OR stock would go negative
                item = self._fetch_item("ID", item_id)
                if item is None:
                    msg = f"Item ID {item_id} not found."
                else:
                    msg = (f"Insufficient stock for Item ID {item_id}. "
                           f"Available={item['inventory']}, Requested={abs(delta)}")
                self._log("ADJUST_QUANTITY", "ERROR", msg)
                return msg

            self._log("ADJUST_QUANTITY", "SUCCESS", f"ID={item_id}, delta={delta:+d}")
            return True

        except Exception as e:
            self._log("ADJUST_QUANTITY", "ERROR", str(e))
            return str(e)

    # Backward-compatible aliases
    def subtract_quantity(self, item_id: int, quantity: int):
        return self.adjust_quantity(item_id, -quantity)

    def add_quantity(self, item_id: int, quantity: int):
        return self.adjust_quantity(item_id, quantity)

    def import_csv_to_db(self, csv_file_path: str):
        """
        Bulk-import a CSV into the inventory table.
        Required columns: id, name, cost, category, inventory.
        Uses executemany() for a single batch insert instead of row-by-row.
        """
        try:
            df = pd.read_csv(csv_file_path)
        except Exception as e:
            return f"Could not read CSV: {e}"

        required = {"id", "name", "cost", "category", "inventory"}
        missing  = required - set(df.columns)
        if missing:
            return f"CSV missing columns: {', '.join(missing)}"

        rows, errors = [], []
        for i, row in df.iterrows():
            err = _validate_item(
                int(row["id"]), str(row["name"]),
                int(row["cost"]), str(row["category"]), int(row["inventory"])
            )
            if err:
                errors.append(f"Row {i + 1}: {err}")
                self._log("IMPORT_CSV", "ROW_ERROR", f"Row {i+1}: {err}")
                continue
            rows.append((int(row["id"]), str(row["name"]),
                         int(row["cost"]), str(row["category"]), int(row["inventory"])))

        if not rows:
            return f"No valid rows to import. Errors: {errors}"

        try:
            with self._get_conn() as (conn, cur):
                cur.executemany(
                    f"INSERT OR IGNORE INTO {self.table} (ID, name, cost, category, inventory) VALUES (?,?,?,?,?)",
                    rows
                )
                conn.commit()
            self._log("IMPORT_CSV", "SUCCESS", f"Imported {len(rows)} rows. Skipped {len(errors)}.")
            return f"Imported {len(rows)} items. {len(errors)} rows skipped."
        except Exception as e:
            self._log("IMPORT_CSV", "ERROR", str(e))
            return str(e)

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def get_item_by_id(self, item_id: int) -> Optional[dict]:
        """Return one item dict {id, name, cost, category, inventory} or None."""
        return self._fetch_item("ID", item_id)

    def get_item_by_name(self, name: str) -> Optional[dict]:
        """Return one item dict {id, name, cost, category, inventory} or None."""
        return self._fetch_item("name", name)

    def show_inventory(self) -> pd.DataFrame:
        """Return the full inventory table as a DataFrame."""
        try:
            with self._get_conn() as (conn, _):
                df = pd.read_sql_query(f"SELECT * FROM {self.table}", conn)
            self._log("SHOW_INVENTORY", "SUCCESS", f"{len(df)} records.")
            return df
        except Exception as e:
            self._log("SHOW_INVENTORY", "ERROR", str(e))
            return pd.DataFrame()

    def search_items(
        self,
        name:     Optional[str]   = None,
        category: Optional[str]   = None,
        min_cost: Optional[float] = None,
        max_cost: Optional[float] = None,
    ) -> pd.DataFrame:
        """Filtered item search; all parameters optional."""
        clauses, params = [], []

        if name:
            clauses.append("name LIKE ?");     params.append(f"%{name}%")
        if category:
            clauses.append("category LIKE ?"); params.append(f"%{category}%")
        if min_cost is not None:
            clauses.append("cost >= ?");       params.append(min_cost)
        if max_cost is not None:
            clauses.append("cost <= ?");       params.append(max_cost)

        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        sql   = f"SELECT * FROM {self.table} {where}"

        try:
            with self._get_conn() as (conn, _):
                df = pd.read_sql_query(sql, conn, params=params)
            self._log("SEARCH_ITEMS", "SUCCESS",
                      f"name={name}, category={category}, min={min_cost}, max={max_cost} → {len(df)} rows")
            return df
        except Exception as e:
            self._log("SEARCH_ITEMS", "ERROR", str(e))
            return pd.DataFrame()

    def fetch_logs(
        self,
        user:       Optional[str]      = None,
        action:     Optional[str]      = None,
        start_date: Optional[datetime] = None,
        end_date:   Optional[datetime] = None,
    ) -> pd.DataFrame:
        """Return filtered log rows as a DataFrame."""
        clauses, params = [], []

        if user:
            clauses.append("user = ?");      params.append(user)
        if action:
            clauses.append("action = ?");    params.append(action)
        if start_date:
            clauses.append("timestamp >= ?");params.append(start_date.strftime("%Y-%m-%d %H:%M:%S"))
        if end_date:
            clauses.append("timestamp <= ?");params.append(end_date.strftime("%Y-%m-%d %H:%M:%S"))

        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        try:
            with self._get_conn(self.log_path) as (conn, _):
                return pd.read_sql_query(f"SELECT * FROM logs {where}", conn, params=params)
        except Exception as e:
            return pd.DataFrame({"error": [str(e)]})

    def prune_logs(self, days_old: int = 30) -> bool:
        """Delete log entries older than `days_old` days."""
        cutoff = (datetime.now() - timedelta(days=days_old)).strftime("%Y-%m-%d %H:%M:%S")
        try:
            with self._get_conn(self.log_path) as (conn, cur):
                cur.execute("DELETE FROM logs WHERE timestamp < ?", (cutoff,))
                deleted = cur.rowcount
                conn.commit()
            self._log("PRUNE_LOGS", "SUCCESS", f"Deleted {deleted} entries older than {days_old}d.")
            return True
        except Exception as e:
            self._log("PRUNE_LOGS", "ERROR", str(e))
            return False

    @staticmethod
    def create_new_db(inv_path: str, db_name: str, table_name: str):
        """
        One-shot factory: create a brand-new inventory database file.
        Returns True or an error string.
        """
        db_path = os.path.join(inv_path, db_name)
        if os.path.exists(db_path):
            return f"Database '{db_name}' already exists."
        try:
            conn = sqlite3.connect(db_path)
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    ID        INTEGER PRIMARY KEY AUTOINCREMENT,
                    name      TEXT    NOT NULL,
                    cost      INTEGER NOT NULL,
                    category  TEXT    NOT NULL,
                    inventory INTEGER NOT NULL CHECK(inventory >= 0)
                )
            """)
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            return str(e)
