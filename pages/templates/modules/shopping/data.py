"""Data access operations for shopping pages."""

import csv
import math
import os
import sqlite3
from contextlib import contextmanager
from decimal import Decimal, InvalidOperation
from typing import Dict

import pandas as pd

from inventory import Inventory
from shop import ShopTransaction
from utils.app_classes.patron import Patron as PatronRecord


class ShopDataMixin(object):
    @staticmethod
    def get_loader():
        """Return a SQL loader for a bounded request-level session."""
        from okada import SQL
        return SQL("halo").get_loader()

    @contextmanager
    def loader_session(self):
        """Yield one SQL loader and close it explicitly after the request."""
        loader = self.get_loader()
        try:
            yield loader
        finally:
            clean_up = getattr(loader, "clean_up", None)
            if callable(clean_up):
                try:
                    clean_up()
                except Exception as exc:
                    self.logger.warning(f"SQL loader cleanup failed: {exc}")

    def _load_sql(self, sql, loader=None):
        if loader is not None:
            return loader.load_data(sql)
        with self.loader_session() as managed_loader:
            return managed_loader.load_data(sql)

    def _normalize_coding_tag(self, tag):
        if isinstance(tag, dict):
            tag = tag.get('tag')
        if tag is None:
            return None
        value = str(tag).strip().casefold().replace("_", "-")
        aliases = {
            "bd na": "na",
            "bd-na": "na",
            "south-east-asia": "sea",
            "southeast-asia": "sea",
        }
        value = aliases.get(value, value)
        return value if value in set(self.config.bdcoding_tags) else None

    def _infer_coding_tag(self, coding):
        value = str(coding or "").strip()
        direct = self._normalize_coding_tag(value)
        if direct:
            return direct

        probe = value.casefold()
        if "japan" in probe:
            return self._normalize_coding_tag("japan")
        if "korea" in probe:
            return self._normalize_coding_tag("korea")
        if "local" in probe:
            return self._normalize_coding_tag("local")
        if "sea" in probe:
            return self._normalize_coding_tag("sea")
        return None

    @staticmethod
    def _parse_override_integer(value):
        text = str(value or "").strip().replace(",", "")
        if not text:
            return None
        try:
            number = Decimal(text)
        except (InvalidOperation, ValueError):
            return None
        if (
            not number.is_finite()
            or number < 0
            or number != number.to_integral_value()
        ):
            return None
        return int(number)

    def _load_override_rows(self):
        """Return normalized optional patron overrides, cached by file version."""
        path = getattr(self.config, "path_override", None)
        if not path:
            return {}

        try:
            stat = os.stat(path)
        except OSError:
            # The entire override facility is opt-in; a missing file means no overrides.
            return {}

        cache_key = (str(path), stat.st_mtime, stat.st_size)
        if getattr(self, "_override_cache_key", None) == cache_key:
            return getattr(self, "_override_cache", {})

        overrides = {}
        try:
            with open(path, "r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                columns = {
                    str(name or "").strip().casefold(): name
                    for name in (reader.fieldnames or ())
                }
                uid_column = columns.get("universalplayerid")
                if not uid_column:
                    raise ValueError(
                        "override CSV requires a universalplayerid column"
                    )

                for row_number, row in enumerate(reader, start=2):
                    uid = self.format_om(row.get(uid_column))
                    if not uid:
                        continue

                    values = dict(overrides.get(uid, {}))
                    for field in ("redemptions", "category", "points"):
                        source_column = columns.get(field)
                        if not source_column:
                            continue
                        raw_value = str(row.get(source_column) or "").strip()
                        if not raw_value:
                            continue
                        parsed = self._parse_override_integer(raw_value)
                        if parsed is None:
                            self.logger.warning(
                                "Ignoring invalid %s override for %s on row %s",
                                field, uid, row_number,
                            )
                            continue
                        values[field] = parsed

                    region_column = columns.get("region")
                    raw_region = (
                        str(row.get(region_column) or "").strip()
                        if region_column else ""
                    )
                    if raw_region:
                        region = self._normalize_coding_tag(raw_region)
                        if region:
                            values["region"] = region
                        else:
                            self.logger.warning(
                                "Ignoring invalid region override for %s on row %s",
                                uid, row_number,
                            )

                    if values:
                        overrides[uid] = values
        except Exception as exc:
            self.logger.warning("Override CSV unavailable: %s", exc)
            overrides = {}

        self._override_cache_key = cache_key
        self._override_cache = overrides
        return overrides

    def get_patron_override(self, uid):
        uid = self.format_om(uid)
        return self._load_override_rows().get(uid, {})

    def get_entitlement_override(self, uid):
        uid = self.format_om(uid)
        override_region = self.get_patron_override(uid).get("region")
        if override_region:
            return override_region
        return self.config.bdcoding_entitlement_overrides.get(uid)

    def get_points_override(self, uid):
        uid = self.format_om(uid)
        override = self.get_patron_override(uid)
        if "points" in override:
            return override["points"]
        return self.config.balance_overrides.get(uid)

    def get_redemption_limit(self, uid):
        uid = self.format_om(uid)
        override = self.get_patron_override(uid)
        if "redemptions" in override:
            return override["redemptions"]
        return self.config.max_redemption

    def get_category_limit(self, uid):
        uid = self.format_om(uid)
        override = self.get_patron_override(uid)
        if "category" in override:
            return override["category"]
        return self.config.max_per_category

    def has_unlimited_redemptions(self, uid):
        uid = self.format_om(uid)
        return uid in self.config.unlimited_redemption_uids

    def get_coding_tag(self, uid: str, loader=None):
        """Return (tag, display_value, source) for optional BD coding mode."""
        if not self.config.bdcoding:
            return self.config.bdcoding_default_tag, "", "disabled"

        uid = self.format_om(uid)
        override_tag = self.get_entitlement_override(uid)
        if override_tag:
            return (
                override_tag,
                "Entitled for {}".format(override_tag.title()),
                "entitlement_override",
            )

        try:
            patron = PatronRecord(uid, loader=loader)
            if hasattr(patron, "get_coding"):
                coding = patron.get_coding()
            else:
                coding = patron.get_bd_tag()
        except Exception as exc:
            self.logger.warning(f"BD coding lookup failed for {uid}: {exc}")
            coding = {"coding": f"Lookup failed [{type(exc).__name__}]: {exc}", "tagging": None, "source": "error"}

        tag = None
        source = "legacy"
        display = coding
        if isinstance(coding, dict):
            source = str(coding.get("source") or "legacy")
            source_key = source.strip().casefold()
            promoter_status = str(coding.get("promoter_status") or "").strip()
            promoter_error = str(coding.get("promoter_error") or "").strip()
            promoter = coding.get("promoter") if isinstance(coding.get("promoter"), dict) else {}
            if source_key == "promoter":
                tag = (
                    self._normalize_coding_tag(promoter.get("tag"))
                    or self._normalize_coding_tag(promoter.get("tagging"))
                    or self._infer_coding_tag(promoter.get("team"))
                    or self._normalize_coding_tag(coding.get("tag"))
                    or self._normalize_coding_tag(coding.get("tagging"))
                )
                display = (
                    coding.get("coding")
                    or promoter.get("team")
                    or promoter.get("tagging")
                    or tag
                )
            else:
                tag = self._normalize_coding_tag(coding.get("tag") or coding.get("tagging"))
                display = coding.get("coding") or coding.get("tagging") or tag

            coding_rows = coding.get("coding_rows") if isinstance(coding.get("coding_rows"), list) else []
            rows_display = ", ".join(str(row) for row in coding_rows if row)
            if promoter_error:
                self.logger.error("Promoter lookup issue for %s: %s", uid, promoter_error)
                source = f"{source} | promoter: error [{promoter_error}]"
            elif promoter_status:
                source = f"{source} | promoter: {promoter_status}"
            if rows_display:
                source = f"{source} | rows: {rows_display}"
        elif isinstance(coding, (list, tuple)):
            for part in coding:
                tag = tag or self._infer_coding_tag(part)
            display = next((str(part) for part in coding if part), tag)
        else:
            tag = self._infer_coding_tag(coding)

        if not tag:
            tag = self._normalize_coding_tag(self.config.bdcoding_default_tag)

        display = str(display or tag or "").strip()
        if not tag:
            return None, display, source

        return tag, display.title(), source

    def _inventory_db_filename(self, coding_tag=None):
        tag = self._normalize_coding_tag(coding_tag)
        if self.config.bdcoding and tag:
            configured = self.config.bdcoding_inventory_filenames.get(tag)
            if configured:
                return configured
            root, ext = os.path.splitext(self.config.db_filename)
            return f"{root}-{tag}{ext or '.db'}"
        return self.config.db_filename

    def _path_db_for_tag(self, coding_tag=None):
        if self.config.bdcoding and coding_tag:
            return os.path.join(self.config.path_inv, self._inventory_db_filename(coding_tag))
        return self.config.path_db

    def get_style_for_tag(self, coding_tag=None):
        tag = self._normalize_coding_tag(coding_tag)
        return self.config.bdcoding_styles.get(tag, self.config.default_style)

    def get_background_style_for_tag(self, coding_tag=None):
        cfg = self.config
        folder = cfg.assets_folder
        tag = self._normalize_coding_tag(coding_tag)
        image_name = cfg.bdcoding_backgrounds.get(tag, "bg.png")
        return {
            "width": "100vw",
            "height": "100vh",
            "position": "relative",
            "backgroundSize": "cover",
            "backgroundPosition": "center",
            "backgroundRepeat": "no-repeat",
            "backgroundAttachment": "scroll" if cfg.low_power_mode else "fixed",
            "backgroundImage": f"url('/assets/{folder}/{image_name}')",
        }

    def read_prize_pool(self, coding_tag=None) -> pd.DataFrame:
        """Read the full prize pool ordered by cost."""
        conn = sqlite3.connect(self._path_db_for_tag(coding_tag))
        try:
            return pd.read_sql_query(
                f"SELECT * FROM {self.config.prize_table} ORDER BY cost ASC", conn
            )
        finally:
            conn.close()

    def get_tier(self, uid: str, loader=None) -> str:
        """
        Return tier name for a given UID.
        Checks the cached CSV snapshot first, then falls back to SQL.
        """
        uid = self.format_om(uid)
        if self.get_entitlement_override(uid):
            return "Entitled"
        # try:
        #     hist = pd.read_csv(self.config.path_tier_csv)
        #     hist["UniversalPlayerID"] = hist["UniversalPlayerID"].astype(str).str.strip()
        #     filtered = hist[hist["UniversalPlayerID"] == uid.strip()]
        #     if not filtered.empty:
        #         return filtered.iloc[0]["Tier"]
        # except Exception as e:
        #     self.logger.warning(f"Tier CSV unavailable, falling back to SQL for {uid}: {e}")

        cfg = self.config
        if cfg.allow_all_tiers:
            sql = f"""
                SELECT p.UniversalPlayerID,
                    COALESCE(NULLIF(LTRIM(RTRIM(tr.TierName)), ''), 'NA') AS TierName
                FROM ENGAGEDB.dbo.UC_PL_Player p
                LEFT JOIN ENGAGEDB.dbo.UC_PL_Tier t ON t.PlayerID = p.PlayerID
                LEFT JOIN ENGAGEDB.dbo.UC_X_Tier tr ON tr.TierID = t.TierID
                WHERE p.UniversalPlayerID = '{uid}'
            """
        else:
            case_clauses = "\n".join(
                f"WHEN TierID = {tier_id} THEN '{name}'"
                for tier_id, name in cfg.tier_names.items()
            )
            tier_id_list = ", ".join(str(t) for t in cfg.valid_tier_ids)
            sql = f"""
                SELECT UniversalPlayerID,
                    CASE
                        {case_clauses}
                        ELSE 'NA'
                    END AS TierName
                FROM ENGAGEDB.dbo.UC_PL_Player p
                LEFT JOIN ENGAGEDB.dbo.UC_PL_Tier t ON t.PlayerID = p.PlayerID
                WHERE UniversalPlayerID = '{uid}'
                  AND t.TierID IN ({tier_id_list})
            """
        result = self._load_sql(sql, loader=loader)
        return result.iloc[0]["TierName"] if not result.empty else "NA"

    def get_balance(self, uid: str, loader=None) -> int:
        """Return total TP earned during the campaign window (ceiling)."""
        uid = self.format_om(uid)
        points_override = self.get_points_override(uid)
        if points_override is not None:
            return points_override

        sql = f"""
            SELECT p.UniversalPlayerID AS uid, tp.PlayerID, SUM(tp.TierPoint) AS Sum_TP
            FROM [ENGAGEDB].[dbo].[UC_PL_Rating] r
            LEFT JOIN [ENGAGEDB].[dbo].[UC_PL_Player] p          ON r.PlayerID   = p.PlayerID
            LEFT JOIN [ENGAGEDB].[dbo].[UC_PL_TierPointDetailActual] tp ON r.RatingID = tp.RatingID
            WHERE r.TransactionDateTime >= '{self.config.campaign_start}'
              AND r.TransactionDateTime  < '{self.config.campaign_end}'
              AND p.UniversalPlayerID = '{uid}'
            GROUP BY p.UniversalPlayerID, tp.PlayerID
            ORDER BY p.UniversalPlayerID, tp.PlayerID
        """
        tp_earn = self._load_sql(sql, loader=loader)
        if tp_earn.empty:
            return 0
        tp_earn = tp_earn[tp_earn["Sum_TP"] > 0]
        tp_earn["uid"] = tp_earn["uid"].str.strip()
        return math.ceil(tp_earn["Sum_TP"].sum())

    def _shop_transaction(self) -> "ShopTransaction":
        return ShopTransaction(
            self.config.path_data, self.config.db_filename,
            self.config.orders_table, user=f"redeem-app-{self.suffix}",
        )

    def _inventory(self, coding_tag=None) -> "Inventory":
        return Inventory(
            self.config.path_inv, self._inventory_db_filename(coding_tag),
            self.config.prize_table, user=f"redeem-app-{self.suffix}",
        )

    def get_redeemed(self, uid: str) -> int:
        """Total TP already redeemed across ALL transactions."""
        return int(self._shop_transaction().get_total_redeemed(uid) or 0)

    def get_redemption_summary(self, uid: str, df: pd.DataFrame):
        """Return total redeemed and category counts using one transaction helper."""
        if self.has_unlimited_redemptions(uid):
            return 0, {}
        shop = self._shop_transaction()
        redeemed = int(shop.get_total_redeemed(uid) or 0)
        name_to_cat = (
            df[["name", "category"]]
            .assign(name=lambda values: values["name"].astype(str).str.strip())
            .drop_duplicates("name")
            .set_index("name")["category"]
            .to_dict()
        )
        window_start, window_end = self.get_redeemed_window()
        category_counts = shop.get_redeemed_by_category(
            uid, name_to_cat, since=window_start, until=window_end
        )
        return redeemed, category_counts

    def get_redeemed_window(self):
        window_start = self.config.redeemed_window_start
        window_end = self.config.redeemed_window_end
        if callable(window_start):
            return window_start()
        if callable(window_end):
            return window_start, window_end()
        return window_start, window_end

    def get_redeemed_per_category(self, uid: str, df: pd.DataFrame) -> Dict[str, int]:
        """Total quantity redeemed per category for a player, within the redeemed window."""
        if self.has_unlimited_redemptions(uid):
            return {}
        name_to_cat: Dict[str, str] = (
            df[["name", "category"]]
            .assign(name=lambda values: values["name"].astype(str).str.strip())
            .drop_duplicates("name")
            .set_index("name")["category"]
            .to_dict()
        )
        window_start, window_end = self.get_redeemed_window()
        return self._shop_transaction().get_redeemed_by_category(
            uid, name_to_cat,
            since=window_start,
            until=window_end,
        )

    def find_initials(self, om_number: str, loader=None) -> str:
        om_number = self.format_om(om_number)
        sql = f"""
            SELECT [FirstName] AS fn, [LastName] AS ln
            FROM [ENGAGEDB].[dbo].[UC_PL_Player]
            WHERE UniversalPlayerID = '{om_number}'
        """
        result = self._load_sql(sql, loader=loader)
        return f"{result.loc[0, 'fn'][0]}.{result.loc[0, 'ln'][0]}."

    # ------------------------------------------------------------
