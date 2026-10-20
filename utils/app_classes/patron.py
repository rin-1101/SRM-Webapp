# patron.py
# class for specific patron
# for dashboard
import re
import math
import os
import logging
import pandas as pd
from datetime import timedelta
import sys
from datetime import datetime

ROOT = "\\\\ominfstdpsd10001p-fs.int.okadamanila.com\\Casino\\Strategic Marketing\\Database Admin\\ETL\\Applications\\okada"
PROMOTER_FILE = r"\\ominfstdpsd10001p-fs.int.okadamanila.com\Casino\Strategic Marketing\Marketing Analysis\Regular Reports\Promoter v2\List of Promoters.xlsx"
sys.path.append(ROOT)
from okada import SQL, SQLService

logger = logging.getLogger(__name__)

class Patron:
    _promoter_cache = None
    _promoter_cache_mtime = None

    def __init__(self, om_number, loader=None):
        self.om_number = self.format_om(om_number)
        self._loader = loader
        self.full_name = None
        self.tier = None
        self.region = None
        self.firstname = None
        self.lastname = None
        self.initials = None      
        self.playerid = None
        self.nationality = None
        self._load_name_data()
        self._set_tier()
        
    def format_om(self,om):
        om_str = str(om).upper()
        if re.fullmatch(r"OM\d{9}", om_str):
            return om_str
        digits = ''.join(filter(str.isdigit, om_str))
        return f"OM{digits.zfill(9)}"

    def _load_sql(self, sql):
        loader = self._loader
        owns_loader = loader is None
        if owns_loader:
            loader = SQL("engage").get_loader()
        try:
            return loader.load_data(sql)
        finally:
            if owns_loader:
                clean_up = getattr(loader, "clean_up", None)
                if callable(clean_up):
                    try:
                        clean_up()
                    except Exception as exc:
                        logger.warning("SQL loader cleanup failed for %s: %s", self.om_number, exc)

    #for player initialization
    def _load_name_data(self):
        sql = f"""
            SELECT 
                [FirstName] AS fn,
                [LastName] AS ln,
                [FullName] AS fullname,
                p.[PlayerID] AS pid,
				nat.Name as nationality
            FROM [ENGAGEDB].[dbo].[UC_PL_Player] p 
			left join ENGAGEDB.dbo.UC_PL_Attribute att
				on att.PlayerID = p.PlayerID
			left join ENGAGEDB.dbo.UC_X_Nationality nat
				on att.NationalityID = nat.NationalityID
            WHERE UniversalPlayerID = '{self.om_number}'
        """
        result = self._load_sql(sql)

        if result.empty:
            self.firstname = ""
            self.lastname = ""
            self.full_name = ""
            self.playerid = ""
            self.initials = ""
            self.nationality = ""
            raise ValueError(f"No player data found for OM number {self.om_number}")
        try:
            self.firstname = result.loc[0, "fn"] or ""
            self.lastname = result.loc[0, "ln"] or ""
            self.full_name = result.loc[0, "fullname"] or ""
            self.playerid = result.loc[0, "pid"] or ""
            nationality = result.loc[0, "nationality"]
            self.nationality = str(nationality).strip() if pd.notna(nationality) else ""
            self.initials = f"{self.firstname[0].upper()}.{self.lastname[0].upper()}." if self.firstname and self.lastname else ""
        except Exception as e:
            raise ValueError(f"Failed to parse player data: {e}")
    def __str__(self):
        return f"{self.full_name} ({self.initials}) - Tier: {self.tier}, Region: {self.region}, OM#: {self.om_number}"
    def _set_tier(self):
        sql = f"""        
            SELECT
                [UniversalPlayerID],
                CASE 
                    WHEN tr.TierName LIKE '%Okada%VIP%' THEN 'Okada VIP'
                    WHEN tr.TierName LIKE '%SLOT%' THEN 'Maharlika'
                    ELSE tr.TierName
                END AS tiergroup
            FROM [ENGAGEDB].[dbo].[UC_PL_Player] pl
            LEFT JOIN [ENGAGEDB].[dbo].[UC_PL_Tier] t
                ON pl.PlayerID = t.PlayerID
            LEFT JOIN ENGAGEDB.dbo.UC_X_Tier tr
                ON tr.TierID = t.TierID
            WHERE UniversalPlayerID = '{self.om_number}'
        """
        result = self._load_sql(sql)
        
        if not result.empty:
            self.tier = result.loc[0, 'tiergroup']
        else:
            self.tier = None  # Optional: Only set to None if nothing is found

        # --- Getters ---
    def get_full_name(self):
        return self.full_name

    def get_tier(self):
        return self.tier

    def get_region(self):
        return self.region

    def get_firstname(self):
        return self.firstname

    def get_lastname(self):
        return self.lastname

    def get_initials(self):
        return self.initials

    def get_playerid(self):
        return self.playerid

    def get_nationality(self):
        return self.nationality
    
    # player functions
    
    def get_tp(self, start, end):
        loader = SQL("engage").get_loader()
        if self.om_number =='OM000000001':
            return 999999
        
        if isinstance(start, str):
            start = datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
        if isinstance(end, str):
            end = datetime.strptime(end, "%Y-%m-%d %H:%M:%S")
        # Ensure datetime formatting
        start_str = start.strftime("%Y-%m-%d %H:%M:%S")
        end_str = end.strftime("%Y-%m-%d %H:%M:%S")
        start_minus_one = (start - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")

        sql = f"""
            SELECT
                tp.TierPoint as tp
                FROM [ENGAGEDB].[dbo].[UC_PL_TierPointDetailActual] tp 
                INNER JOIN [ENGAGEDB].[dbo].[UC_PL_Rating] r 
                ON tp.RatingID = r.RatingID 
                INNER JOIN [ENGAGEDB].[dbo].[UC_PL_Player] p 
                ON tp.PlayerID = p.PlayerID 
                WHERE r.TransactionDateTime BETWEEN '{start_str}' AND '{end_str}'
                    AND tp.TransactionDate between '{start_minus_one}' and '{end_str}'
                    AND p.UniversalPlayerID = '{self.om_number}'
        """
        # return sql
        tp_earn = loader.load_data(sql)
        if tp_earn.empty:
            return 0
        return math.ceil(tp_earn['tp'].sum())
    
    def get_cp(self):
        loader = SQL("engage").get_loader()
        if self.om_number =='OM000000001':
            return 999999
        sql = f"""
        SELECT 
            CASE 
                WHEN balancetypeid IN (2,4) THEN balance * -1 
                ELSE balance 
            END AS Balance
        FROM ENGAGEDB.dbo.UC_PL_PointBalance ba
        LEFT JOIN ENGAGEDB.dbo.UC_PL_Player p
            ON p.PlayerID = ba.PlayerID
        WHERE p.UniversalPlayerID = '{self.om_number}'
          AND BucketID = 10030
        """
        balance = loader.load_data(sql)

        if not balance.empty:
            # Sum all relevant balances just in case there are multiple rows
            return balance['Balance'].sum()

        return 0
    def _get_bd_region(self):
        bdlistpath = r"\\ominfstdpsd10001p-fs.int.okadamanila.com\Casino\Casino Marketing\CRM Reports\CM List\BD Earn and Get 082026\BDTAGGING.xlsx"
        bdlist = pd.read_excel(bdlistpath, engine="openpyxl")
        bdlist['UniversalPlayerID'] = bdlist['UniversalPlayerID'].astype(str).str.upper()
        bdlist['Region'] = bdlist['Region'].astype(str).str.upper()
        region_row = bdlist[bdlist['UniversalPlayerID'] == self.om_number]
        if not region_row.empty:
            return region_row.iloc[0]['Region']
        return None
    def _get_bd_coding_rows(self):
        ql = f"""
        SELECT host.firstname + ' ' + host.lastname as coding
            FROM ENGAGEDB.DBO.uc_pl_playerhost player_host
            LEFT JOIN ENGAGEDB.DBO.uc_pl_player player
            ON player_host.playerid = player.playerid
            LEFT JOIN ENGAGEDB.DBO.uc_pl_playerhostdetail host_detail
            ON player_host.id = host_detail.playerhostid
            LEFT JOIN ENGAGEDB.DBO.uc_h_host host
            ON host_detail.hostid = host.id
            WHERE player_host.active = 1
            AND host_detail.active = 1
            AND UniversalPlayerID = '{self.om_number}'
        """
        res = self._load_sql(ql)
        if res.empty or "coding" not in res.columns:
            return []
        return [
            str(coding).strip()
            for coding in res["coding"].tolist()
            if pd.notna(coding) and str(coding).strip()
        ]

    def _get_bd_coding_row(self):
        rows = self._get_bd_coding_rows()
        return rows[0] if rows else ""

    @staticmethod
    def _map_bd_coding_tag(coding):
        coding = str(coding or "").strip().casefold()
        coding_key = re.sub(r"[^a-z0-9]+", "", coding)
        if "japan" in coding or "norisakuhara" in coding_key:
            return "japan"
        if "korea" in coding:
            return "korea"
        if "local" in coding:
            return "local"
        if "sea" in coding:
            return "sea"
        return None


    @staticmethod
    def _map_promoter_team_tag(team):
        team = str(team or "").strip().casefold()
        if team == "korean":
            return "korea"
        if team == "local":
            return "local"
        if team in {"japan", "japanese"}:
            return "japan"
        return "sea"

    @staticmethod
    def _normalize_promoter_coding(coding):
        return re.sub(r"[^a-z0-9]+", "", str(coding or "").casefold())

    @classmethod
    def _map_promoter_tag(cls, coding, team):
        if "norisakuhara" in cls._normalize_promoter_coding(coding):
            return "japan"
        return cls._map_promoter_team_tag(team)

    @staticmethod
    def _clean_promoter_cell(value):
        return "" if pd.isna(value) else str(value).strip()

    @classmethod
    def _load_promoters(cls):
        modified_at = os.path.getmtime(PROMOTER_FILE)
        if (
            cls._promoter_cache is not None
            and cls._promoter_cache_mtime == modified_at
        ):
            return cls._promoter_cache

        promoter = pd.read_excel(PROMOTER_FILE, engine="openpyxl")
        if len(promoter.columns) != 5:
            raise ValueError(
                f"Expected 5 promoter columns, found {len(promoter.columns)}"
            )
        promoter.columns = ["coding", "name", "tm", "team", "universalplayerid"]
        promoter["_coding_key"] = promoter["coding"].map(
            cls._normalize_promoter_coding
        )
        cls._promoter_cache = promoter
        cls._promoter_cache_mtime = modified_at
        return promoter

    @classmethod
    def _get_promoter_match(cls, coding):
        coding_key = cls._normalize_promoter_coding(coding)
        if not coding_key:
            return None
        promoter = cls._load_promoters()

        matches = promoter[promoter["_coding_key"] == coding_key]
        if matches.empty:
            return None

        row = matches.iloc[0]
        team = cls._clean_promoter_cell(row["team"])
        return {
            "tagging": cls._map_promoter_tag(coding, team),
            "name": cls._clean_promoter_cell(row["name"]),
            "tm": cls._clean_promoter_cell(row["tm"]),
            "team": team,
        }

    @classmethod
    def _get_promoter_match_from_rows(cls, codings):
        promoter = cls._load_promoters()
        for coding in codings:
            coding_key = cls._normalize_promoter_coding(coding)
            if not coding_key:
                continue
            matches = promoter[promoter["_coding_key"] == coding_key]
            if matches.empty:
                continue
            row = matches.iloc[0]
            team = cls._clean_promoter_cell(row["team"])
            return coding, {
                "tagging": cls._map_promoter_tag(coding, team),
                "name": cls._clean_promoter_cell(row["name"]),
                "tm": cls._clean_promoter_cell(row["tm"]),
                "team": team,
            }
        return "", None

    def get_bd_tag(self):
        return self.get_coding()["tagging"]

    def get_coding(self):
        # main read excel
        
        bdregion = self._get_bd_region()
        if bdregion:
            return {
                "coding": bdregion,
                "tagging": bdregion,
                "source": "bd_region_list",
                "promoter_status": "not_checked",
                "promoter_error": "",
                "coding_rows": [],
            }
        # else :
        #     return {
        #         "coding": bdregion,
        #         "tagging": bdregion,
        #         "source": "bd_region_list",
        #         "promoter_status": "not_checked",
        #         "promoter_error": "",
        #         "coding_rows": [],
        #     }

        # fallback
        codings = self._get_bd_coding_rows()
        promoter_status = "not_checked"
        promoter_error = ""
        try:
            coding, promoter_match = self._get_promoter_match_from_rows(codings)
            promoter_status = "matched" if promoter_match else "no_match"
        except Exception as exc:
            coding = ""
            promoter_match = None
            promoter_status = "error"
            promoter_error = f"{type(exc).__name__}: {exc}"
            logger.exception(
                "Promoter lookup failed for %s using %s",
                self.om_number,
                PROMOTER_FILE,
            )

        if promoter_match:
            return {
                "coding": coding,
                "tagging": promoter_match["tagging"],
                "source": "promoter",
                "promoter": promoter_match,
                "promoter_status": promoter_status,
                "coding_rows": codings,
            }

        for coding in codings:
            coding_tag = self._map_bd_coding_tag(coding)
            if coding_tag:
                return {
                    "coding": coding,
                    "tagging": coding_tag,
                    "source": "bd_coding",
                    "promoter_status": promoter_status,
                    "promoter_error": promoter_error,
                    "coding_rows": codings,
                }
        return {
            "coding": "",
            "tagging": None,
            "source": "uncoded",
            "promoter_status": promoter_status,
            "promoter_error": promoter_error,
            "coding_rows": codings,
        }

    def get_lp(self):
        return 0
    def get_fp(self):
        return 0
    def get_dom(self):
        return 'BOTH'
    def get_om(self):
        return self.om_number
    def to_dict(self):
        return {
            "om_number": self.om_number,
            "full_name": self.full_name,
            "tier": self.tier,
            "region": self.region,
            "firstname": self.firstname,
            "lastname": self.lastname,
            "initials": self.initials,
            "playerid": self.playerid,
            "nationality": self.nationality
        }
    @staticmethod
    def from_dict(data):
        # Reconstructs Patron object using only `om_number`
        return Patron(data["om_number"])
    
    
