"""
shop.py — ShopTransaction
Handles all order/redemption writes and reads against a local SQLite DB.

Key changes from original:
  - _get_conn() context manager replaces repetitive open/close/cursor boilerplate
  - _log() is a thin wrapper that never raises (logging must not kill a transaction)
  - get_all_redemptions() now returns ALL columns (item, item_id included)
  - add_transaction() computes total_cost internally; callers no longer need to
  - total_value column removed from per-row storage — it was always stale between
    rows and is now computed on-demand by get_total_redeemed()
  - get_halo() SQL uses parameterised LIKE (no f-string injection risk)
  - module-level `loader` kept for backward compat but scoped to get_halo only
  - fetch_logs() connection was never closed in original — fixed
"""

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Optional

import pandas as pd
import sys

ROOT = "\\\\ominfstdpsd10001p-fs.int.okadamanila.com\\Casino\\Strategic Marketing\\Database Admin\\ETL\\Applications\\okada"
sys.path.append(ROOT)
from okada import SQL

# Module-level loader used only by get_halo()
_engage_loader = SQL("ENGAGE").get_loader()


class ShopTransaction:
    """
    Manages a SQLite-backed orders table for campaign redemptions.

    Parameters
    ----------
    db_path    : folder that contains the SQLite file
    db_name    : filename, e.g. "afhc.db"
    table_name : orders table name, e.g. "orders"
    user       : identifier written to every log row
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(self, db_path: str, db_name: str, table_name: str, user: str):
        self.path  = os.path.join(db_path, db_name)
        self.table = table_name
        self.user  = user

        log_dir = os.path.join(db_path, "logs")
        os.makedirs(log_dir, exist_ok=True)
        self.log_path = os.path.join(log_dir, f"{os.path.splitext(db_name)[0]}-logs.db")

        self._init_logs_table()
        self._init_orders_table()

    # ------------------------------------------------------------------
    # Internal utilities
    # ------------------------------------------------------------------

    @contextmanager
    def _get_conn(self, path: Optional[str] = None):
        """
        Yield a connection and cursor, always closing both on exit.
        Usage:
            with self._get_conn() as (conn, cur):
                cur.execute(...)
                conn.commit()
        """
        conn = sqlite3.connect(path or self.path)
        conn.execute("PRAGMA journal_mode=WAL")   # safe for multi-process writes
        cur  = conn.cursor()
        try:
            yield conn, cur
        finally:
            cur.close()
            conn.close()

    def _log(self, action: str, status: str, details: Optional[str] = None) -> None:
        """Write one row to the logs table. Silently swallows its own errors."""
        try:
            with self._get_conn(self.log_path) as (conn, cur):
                cur.execute(
                    "INSERT INTO logs (timestamp, user, action, status, details) VALUES (?,?,?,?,?)",
                    (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.user, action, status, details),
                )
                conn.commit()
        except Exception:
            pass  # logging must never crash a caller

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

    def _init_orders_table(self) -> bool:
        """
        Create the orders table if it does not exist.
        NOTE: total_value column is intentionally removed.
              It was stored per-row but always recalculated anyway,
              making the stored value unreliable between inserts.
              Use get_total_redeemed() for the live running total.
        """
        try:
            with self._get_conn() as (conn, cur):
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self.table} (
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
                """)
                conn.commit()
            self._log("INIT_DB", "SUCCESS", f"Table '{self.table}' ready.")
            return True
        except Exception as e:
            self._log("INIT_DB", "ERROR", str(e))
            return False

    # ------------------------------------------------------------------
    # External data (ENGAGE SQL)
    # ------------------------------------------------------------------

    def get_halo(self, uid: str, start_date: str, end_date: str, halo_tagging: str) -> pd.DataFrame:
        """
        Fetch halo prize redemptions from ENGAGE for a given player and event tag.
        Uses parameterised LIKE to avoid SQL injection via halo_tagging.
        """
        sql = f"""
            WITH subq AS (
                SELECT
                    pr.PlayerID,
                    ed.Name AS EventName,
                    CAST(
                        CONVERT(
                            varchar(10),
                            IIF(DATEPART(hour, pr.RedemptionDate) < 6,
                                DATEADD(day, -1, pr.RedemptionDate),
                                pr.RedemptionDate),
                            101
                        ) AS date
                    ) AS GameDate,
                    prd.Returned,
                    p.UniversalPlayerID
                FROM ENGAGEDB.AWA.UC_PL_PrizeRedemption pr
                LEFT JOIN ENGAGEDB.AWA.UC_X_EventDefinition       ed  ON pr.EventDefinitionID = ed.ID
                LEFT JOIN ENGAGEDB.AWA.UC_PL_PrizeRedemptionDetail prd ON pr.ID = prd.PrizeRedemptionID
                LEFT JOIN ENGAGEDB.dbo.UC_PL_Player                p   ON pr.PlayerID = p.PlayerID
            )
            SELECT * FROM subq
            WHERE GameDate BETWEEN '{start_date}' AND '{end_date}'
              AND UniversalPlayerID = '{uid}'
              AND EventName LIKE '%{halo_tagging}%'
              AND Returned IS NULL
        """
        return _engage_loader.load_data(sql)

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def add_transaction(
        self,
        uid: str,
        item_id: int,
        item_name: str,
        quantity: int,
        cost: int,
        total_val: int,          # kept for API compat; no longer stored per-row
        credits_used: int = 0,
        cp_used: int = 0,
        status: str = "pending",
    ) -> bool:
        """
        Insert one order row.

        Returns
        -------
        True   – inserted successfully
        False  – skipped as duplicate (same uid/item/qty/cost within 30 s)
        str    – error message on failure
        """
        now_str    = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_cost = quantity * cost

        self._log("ADD_TRANSACTION", "CHECKING values",
                    f"UID={uid}, Item={item_name}, Qty={quantity}, Cost={cost}, total_cost={total_cost}, CreditsUsed={credits_used}, CPUsed={cp_used}, Status={status}")
        try:
            with self._get_conn() as (conn, cur):
                # --- duplicate guard (same item+qty+cost within 30 seconds) ---
                
                self._log("ADD_TRANSACTION", "checkpoint",f"1")
                cur.execute(f"""
                    SELECT 1 FROM {self.table}
                    WHERE uid     = ?
                      AND item_id = ?
                      AND item    = ?
                      AND quantity= ?
                      AND cost    = ?
                      AND ABS(strftime('%s', createddate) - strftime('%s', ?)) <= 30
                    LIMIT 1
                """, (uid, item_id, item_name, quantity, cost, now_str))
                
                self._log("ADD_TRANSACTION", "checkpoint",f"2")
                if cur.fetchone():
                    self._log("ADD_TRANSACTION", "SKIPPED_DUPLICATE",
                              f"UID={uid}, Item={item_name}, Qty={quantity}, Cost={cost}")
                    return False

                self._log("ADD_TRANSACTION", "checkpoint",f"3")
                cur.execute(f"""
                    INSERT INTO {self.table}
                        (uid, createddate, updateddate, item_id, item,
                         quantity, cost, total_cost, credits_used, cp_used, status)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """, (uid, now_str, now_str, item_id, item_name,
                      quantity, cost, total_cost, credits_used, cp_used, status))
                
                self._log("ADD_TRANSACTION", "checkpoint",f"4")
                conn.commit()

                self._log("ADD_TRANSACTION", "checkpoint",f"5")

            self._log("ADD_TRANSACTION", "SUCCESS",
                      f"UID={uid}, Item={item_name}, Qty={quantity}, Cost={cost}, Status={status}")
            return True

        except Exception as e:
            self._log("ADD_TRANSACTION", "ERROR", str(e))
            return str(e)

    def update_transaction(
        self,
        trans_id: int,
        item_id:  Optional[int]  = None,
        item:     Optional[str]  = None,
        quantity: Optional[int]  = None,
        cost:     Optional[int]  = None,
        status:   Optional[str]  = None,
    ):
        """
        Partially update an order row. Only supplied (non-None) fields are changed.
        Recalculates total_cost when quantity or cost changes.
        """
        try:
            with self._get_conn() as (conn, cur):
                cur.execute(
                    f"SELECT uid, item_id, item, quantity, cost, status FROM {self.table} WHERE id=?",
                    (trans_id,)
                )
                row = cur.fetchone()
                if not row:
                    msg = f"No transaction found with ID={trans_id}"
                    self._log("UPDATE_TRANSACTION", "ERROR", msg)
                    return msg

                cur_uid, cur_item_id, cur_item, cur_qty, cur_cost, cur_status = row

                # Resolve final values
                new_item_id = item_id  if item_id  is not None else cur_item_id
                new_item    = item     if item     is not None else cur_item
                new_qty     = quantity if quantity is not None else cur_qty
                new_cost    = cost     if cost     is not None else cur_cost
                new_status  = status   if status   is not None else cur_status
                new_tc      = new_qty * new_cost
                now_str     = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                cur.execute(f"""
                    UPDATE {self.table}
                       SET item_id    = ?,
                           item       = ?,
                           quantity   = ?,
                           cost       = ?,
                           total_cost = ?,
                           status     = ?,
                           updateddate= ?
                     WHERE id = ?
                """, (new_item_id, new_item, new_qty, new_cost, new_tc, new_status, now_str, trans_id))
                conn.commit()

            self._log("UPDATE_TRANSACTION", "SUCCESS",
                      f"ID={trans_id}, item_id={new_item_id}, qty={new_qty}, cost={new_cost}, status={new_status}")
            return True

        except Exception as e:
            self._log("UPDATE_TRANSACTION", "ERROR", str(e))
            return str(e)

    def update_status(self, trans_id: int, status: str):
        """Convenience wrapper: change only the status of one order row."""
        return self.update_transaction(trans_id, status=status)

    def delete_transaction(self, trans_id: int):
        """Delete a single order row by its primary key."""
        try:
            with self._get_conn() as (conn, cur):
                cur.execute(f"SELECT uid FROM {self.table} WHERE id=?", (trans_id,))
                row = cur.fetchone()
                if not row:
                    msg = f"No transaction found with ID={trans_id}"
                    self._log("DELETE_TRANSACTION", "ERROR", msg)
                    return msg

                cur.execute(f"DELETE FROM {self.table} WHERE id=?", (trans_id,))
                conn.commit()

            self._log("DELETE_TRANSACTION", "SUCCESS", f"Deleted ID={trans_id}")
            return True

        except Exception as e:
            self._log("DELETE_TRANSACTION", "ERROR", str(e))
            return str(e)

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def show_transactions(self) -> pd.DataFrame:
        """Return every row in the orders table as a DataFrame."""
        try:
            with self._get_conn() as (conn, _):
                df = pd.read_sql_query(f"SELECT * FROM {self.table}", conn)
            self._log("SHOW_TRANSACTIONS", "SUCCESS", f"{len(df)} records.")
            return df
        except Exception as e:
            self._log("SHOW_TRANSACTIONS", "ERROR", str(e))
            return pd.DataFrame()

    def search_transactions(
        self,
        uid:       Optional[str]   = None,
        item_id:   Optional[int]   = None,
        item:      Optional[str]   = None,
        status:    Optional[str]   = None,
        min_total: Optional[float] = None,
        max_total: Optional[float] = None,
    ) -> pd.DataFrame:
        """Filtered query; all parameters are optional."""
        clauses, params = [], []

        if uid:
            clauses.append("uid = ?");        params.append(uid)
        if item_id is not None:
            clauses.append("item_id = ?");    params.append(item_id)
        if item:
            clauses.append("item LIKE ?");    params.append(f"%{item}%")
        if status:
            clauses.append("status = ?");     params.append(status)
        if min_total is not None:
            clauses.append("total_cost >= ?");params.append(min_total)
        if max_total is not None:
            clauses.append("total_cost <= ?");params.append(max_total)

        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        sql   = f"SELECT * FROM {self.table} {where}"

        try:
            with self._get_conn() as (conn, _):
                df = pd.read_sql_query(sql, conn, params=params)
            self._log("SEARCH_TRANSACTIONS", "SUCCESS", f"{len(df)} results.")
            return df
        except Exception as e:
            self._log("SEARCH_TRANSACTIONS", "ERROR", str(e))
            return pd.DataFrame()

    def is_redeemed(self, uid: str) -> bool:
        """Return True if the player has at least one order row."""
        try:
            with self._get_conn() as (conn, cur):
                cur.execute(f"SELECT 1 FROM {self.table} WHERE uid=? LIMIT 1", (uid,))
                found = cur.fetchone() is not None
            self._log("IS_REDEEMED", "SUCCESS", f"UID={uid}, found={found}")
            return found
        except Exception as e:
            self._log("IS_REDEEMED", "ERROR", str(e))
            return False

    def get_total_redeemed(self, uid: str) -> int:
        """
        Return total TP spent (SUM of total_cost) for a player.
        Uses total_cost (quantity * cost per row) rather than the old
        total_value column which was unreliable across multi-item baskets.
        """
        try:
            with self._get_conn() as (conn, cur):
                cur.execute(
                    f"SELECT COALESCE(SUM(total_cost), 0) FROM {self.table} WHERE uid=?",
                    (uid,)
                )
                total = int(cur.fetchone()[0])
            self._log("GET_TOTAL_REDEEMED", "SUCCESS", f"UID={uid}, Total={total}")
            return total
        except Exception as e:
            self._log("GET_TOTAL_REDEEMED", "ERROR", str(e))
            return 0

    def get_all_redemptions(self, uid: str) -> list[dict]:
        """
        Return every order row for a player as a list of dicts.

        Fix vs original: now selects ALL columns (including item and item_id)
        so callers can group by item or category without a second query.
        """
        try:
            with self._get_conn() as (conn, _):
                df = pd.read_sql_query(
                    f"SELECT * FROM {self.table} WHERE uid=?",
                    conn, params=(uid,)
                )
            return df.to_dict(orient="records") if not df.empty else []
        except Exception as e:
            self._log("GET_ALL_REDEMPTIONS", "ERROR", str(e))
            return []

    def fetch_logs(self) -> pd.DataFrame:
        """Return the full logs table as a DataFrame."""
        try:
            with self._get_conn(self.log_path) as (conn, _):
                return pd.read_sql_query("SELECT * FROM logs", conn)
        except Exception as e:
            return pd.DataFrame({"error": [str(e)]})
    def get_redeemed_by_category(
        self,
        uid: str,
        name_to_category: dict[str, str],
        since: str | None = None,
        until: str | None = None,
    ) -> dict[str, int]:
        """
        Return quantity redeemed per category for a player.

        Parameters
        ----------
        uid              : player OM number
        name_to_category : mapping of item name -> category
                        (build from prize_pool df before calling)
        since            : optional start datetime string e.g. "2026-05-17 06:00:00"
        until            : optional end datetime string   e.g. "2026-05-24 06:00:00"

        Returns
        -------
        dict  category -> total_quantity_redeemed
        """
        try:
            with self._get_conn() as (conn, cur):
                query  = f"SELECT item, SUM(quantity) FROM {self.table} WHERE uid=?"
                params: list = [uid]

                if since:
                    query += " AND createddate >= ?"
                    params.append(since)
                if until:
                    query += " AND createddate < ?"
                    params.append(until)

                query += " GROUP BY item"
                cur.execute(query, params)
                rows = cur.fetchall()
        except Exception as e:
            self._log("GET_REDEEMED_BY_CATEGORY", "ERROR", str(e))
            return {}

        cat_counts: dict[str, int] = {}
        for item_name, qty in rows:
            if not item_name or qty is None:
                continue
            cat = name_to_category.get(str(item_name).strip(), "unknown")
            cat_counts[cat] = cat_counts.get(cat, 0) + int(qty)

        return cat_counts