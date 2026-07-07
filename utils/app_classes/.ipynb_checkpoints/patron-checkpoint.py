# patron.py
# class for specific patron
# for dashboard
import re
import math
import pandas as pd
from datetime import timedelta
import sys
from datetime import datetime

ROOT = "\\\\ominfstdpsd10001p-fs.int.okadamanila.com\\Casino\\Strategic Marketing\\Database Admin\\ETL\\Applications\\okada"
sys.path.append(ROOT)
from okada import SQL, SQLService
loader = SQL("halo").get_loader()

class Patron:
    def __init__(self, om_number):
        self.om_number = self.format_om(om_number)
        self.full_name = None
        self.tier = None
        self.region = None
        self.firstname = None
        self.lastname = None
        self.initials = None      
        self.playerid = None
        self._load_name_data()
        self._set_tier()
        
    def format_om(self,om):
        om_str = str(om).upper()
        if re.fullmatch(r"OM\d{9}", om_str):
            return om_str
        digits = ''.join(filter(str.isdigit, om_str))
        return f"OM{digits.zfill(9)}"
    #for player initialization
    def _load_name_data(self):
        sql = f"""
            SELECT 
                [FirstName] AS fn,
                [LastName] AS ln,
                [FullName] AS fullname,
                [PlayerID] AS pid
            FROM [HALOCOREDB].[dbo].[UC_PL_Player]
            WHERE UniversalPlayerID = '{self.om_number}'
        """
        result = loader.load_data(sql)

        if result.empty:
            self.firstname = ""
            self.lastname = ""
            self.full_name = ""
            self.playerid = ""
            self.initials = ""
            raise ValueError(f"No player data found for OM number {self.om_number}")
        try:
            self.firstname = result.loc[0, "fn"] or ""
            self.lastname = result.loc[0, "ln"] or ""
            self.full_name = result.loc[0, "fullname"] or ""
            self.playerid = result.loc[0, "pid"] or ""
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
            FROM [HALOCOREDB].[dbo].[UC_PL_Player] pl
            LEFT JOIN [HALOCOREDB].[dbo].[UC_PL_Tier] t
                ON pl.PlayerID = t.PlayerID
            LEFT JOIN HALOCOREDB.dbo.UC_X_Tier tr
                ON tr.TierID = t.TierID
            WHERE UniversalPlayerID = '{self.om_number}'
        """
        result = loader.load_data(sql)
        
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
    
    # player functions
    
    def get_tp(self, start, end):
        loader = SQL("halo").get_loader()
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
                FROM [HALOCOREDB].[dbo].[UC_PL_TierPointDetailActual] tp 
                INNER JOIN [HALOCOREDB].[dbo].[UC_PL_Rating] r 
                ON tp.RatingID = r.RatingID 
                INNER JOIN [HALOCOREDB].[dbo].[UC_PL_Player] p 
                ON tp.PlayerID = p.PlayerID 
                WHERE r.TransactionDateTime BETWEEN '{start_str}' AND '{end_str}'
                    AND tp.TransactionDate >= '{start_minus_one}'
                    AND p.UniversalPlayerID = '{self.om_number}'
        """
        # return sql
        tp_earn = loader.load_data(sql)
        if tp_earn.empty:
            return 0
        return math.ceil(tp_earn['tp'].sum())
    
    def get_cp(self):
        if self.om_number =='OM000000001':
            return 999999
        sql = f"""
        SELECT 
            CASE 
                WHEN balancetypeid IN (2,4) THEN balance * -1 
                ELSE balance 
            END AS Balance
        FROM HALOCOREDB.dbo.UC_PL_PointBalance ba
        LEFT JOIN HALOCOREDB.dbo.UC_PL_Player p
            ON p.PlayerID = ba.PlayerID
        WHERE p.UniversalPlayerID = '{self.om_number}'
          AND BucketID = 10030
        """
        balance = loader.load_data(sql)

        if not balance.empty:
            # Sum all relevant balances just in case there are multiple rows
            return balance['Balance'].sum()

        return 0
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
            "playerid": self.playerid
        }
    @staticmethod
    def from_dict(data):
        # Reconstructs Patron object using only `om_number`
        return Patron(data["om_number"])
    
    